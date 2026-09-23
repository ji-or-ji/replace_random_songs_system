using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace RandomSongs.Core;

/// <summary>
/// 从文件夹批量导入：扫描音频文件，并从文件名推断歌名与歌手。
/// 支持常见格式：<c>歌手 - 歌名</c>、<c>歌名 - 歌手</c>、<c>歌手《歌名》</c>、
/// <c>[歌手] 歌名</c>、<c>歌名 (歌手)</c>、带音轨号前缀等；
/// 若某一侧命中「已知歌手」（来自现有歌单），会自动校正被调换的顺序。
/// </summary>
public static class FolderImportService
{
    public const string ImportRequester = "本地导入";

    public static readonly string[] AudioExtensions =
    {
        ".mp3", ".flac", ".m4a", ".wav", ".aac", ".ogg", ".wma", ".ape", ".opus", ".m4b",
    };

    private static readonly string[] Separators = { " - ", " – ", " — ", "-", "–", "—", "_", "|", "｜" };

    public sealed class ParsedFile
    {
        public string FilePath { get; init; } = "";
        public string FileName { get; init; } = "";
        public string SongName { get; set; } = "";
        public string Artist { get; set; } = "";
        public string Note { get; init; } = "";
    }

    /// <summary>收集现有各歌单里出现过的歌手名（用于校正调换的顺序），不写盘。</summary>
    public static HashSet<string> CollectKnownArtists()
    {
        var artists = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var kv in ConfigService.GetPlaylists())
        {
            var file = YamlStore.Load<SongFile>(AppPaths.SongsFile(kv.Key));
            foreach (var song in file?.Songs ?? new List<Song>())
            {
                if (!string.IsNullOrWhiteSpace(song.Artist))
                {
                    artists.Add(song.Artist.Trim());
                }
            }
        }
        return artists;
    }

    public static List<ParsedFile> ScanFolder(
        string folder,
        bool recursive = false,
        bool artistFirst = true,
        ISet<string> knownArtists = null)
    {
        if (!Directory.Exists(folder))
        {
            throw new DirectoryNotFoundException($"文件夹不存在: {folder}");
        }

        var option = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
        var known = knownArtists == null
            ? new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            : new HashSet<string>(
                knownArtists.Where(a => !string.IsNullOrWhiteSpace(a)), StringComparer.OrdinalIgnoreCase);

        return Directory.EnumerateFiles(folder, "*", option)
            .Where(path => AudioExtensions.Contains(Path.GetExtension(path).ToLowerInvariant()))
            .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
            .Select(path => ParseFile(path, artistFirst, known))
            .ToList();
    }

    public static ParsedFile ParseFile(string path, bool artistFirst, ISet<string> knownArtists = null)
    {
        var known = knownArtists ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var (songName, artist, note) = ParseName(Path.GetFileNameWithoutExtension(path), artistFirst, known);
        return new ParsedFile
        {
            FilePath = path,
            FileName = Path.GetFileName(path),
            SongName = songName,
            Artist = artist,
            Note = note,
        };
    }

    /// <summary>从文件名（不含扩展名）推断歌名与歌手。</summary>
    public static (string SongName, string Artist, string Note) ParseName(
        string raw,
        bool artistFirst,
        ISet<string> knownArtists = null)
    {
        var known = knownArtists ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var text = (raw ?? "").Replace('\u3000', ' ').Trim();

        // 去前导音轨号：形如 "01. " / "01 - " / "1_" / "[01] "
        text = Regex.Replace(
            text,
            @"^(?:\s*[\[\(]\d{1,4}[\]\)][\s.\-_|｜]*|\d{1,4}[\s.\-_|｜]+)+",
            "");
        text = text.Trim();
        if (text.Length == 0)
        {
            return (raw?.Trim() ?? "", "", "空文件名");
        }

        // 歌手《歌名》
        var match = Regex.Match(text, @"^(?<a>.+?)\s*[《<](?<t>.+?)[》>]\s*$");
        if (match.Success)
        {
            return (match.Groups["t"].Value.Trim(), match.Groups["a"].Value.Trim(), "《歌名》格式");
        }

        // [歌手] 歌名
        match = Regex.Match(text, @"^\s*\[(?<a>[^\]]+)\]\s*(?<t>.+)$");
        if (match.Success)
        {
            return (match.Groups["t"].Value.Trim(), match.Groups["a"].Value.Trim(), "[]格式");
        }

        // 分隔符二分（含调换校正）
        foreach (var separator in Separators)
        {
            var index = text.IndexOf(separator, StringComparison.Ordinal);
            if (index <= 0)
            {
                continue;
            }
            var left = text[..index].Trim();
            var right = text[(index + separator.Length)..].Trim();
            if (left.Length == 0 || right.Length == 0)
            {
                continue;
            }

            var leftKnown = known.Contains(left);
            var rightKnown = known.Contains(right);
            if (leftKnown && !rightKnown)
            {
                return (right, left, "已知歌手校正");
            }
            if (rightKnown && !leftKnown)
            {
                return (left, right, "已知歌手校正");
            }
            return artistFirst ? (right, left, "") : (left, right, "");
        }

        // 兜底：歌名 (歌手)
        match = Regex.Match(text, @"^(?<t>.+?)\s*[\(（](?<a>[^\)）]+)[\)）]\s*$");
        if (match.Success)
        {
            return (match.Groups["t"].Value.Trim(), match.Groups["a"].Value.Trim(), "()格式·请确认");
        }

        return (text, "", "未识别出歌手");
    }

    /// <summary>把解析结果合并进指定歌单（按 歌名+歌手 去重），返回新增数量。</summary>
    public static int ImportIntoPlaylist(string playlistId, IEnumerable<ParsedFile> files)
    {
        var songs = SongService.LoadSongs(playlistId);
        var existing = songs.Select(DedupKey).ToHashSet();

        var added = 0;
        foreach (var file in files)
        {
            var song = SongService.Normalize(new Song
            {
                SongName = file.SongName,
                Artist = file.Artist,
                LocalPath = file.FilePath,
                RequestedBy = ImportRequester,
            });
            if (!existing.Add(DedupKey(song)))
            {
                continue;
            }
            songs.Add(song);
            added++;
        }
        SongService.SaveSongs(playlistId, songs);
        return added;
    }

    public static (string PlaylistId, int Count) ImportAsNewPlaylist(
        string name,
        string folder,
        IEnumerable<ParsedFile> files)
    {
        var playlistId = PlaylistService.CreatePlaylist(name, $"从文件夹导入: {folder}");
        var count = ImportIntoPlaylist(playlistId, files);
        return (playlistId, count);
    }

    private static string DedupKey(Song song)
        => $"{(song.SongName ?? "").Trim().ToLowerInvariant()}\u0001{(song.Artist ?? "").Trim().ToLowerInvariant()}";
}
