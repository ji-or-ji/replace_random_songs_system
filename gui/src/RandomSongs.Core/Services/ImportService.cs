using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace RandomSongs.Core;

/// <summary>从外部文件导入歌单：支持 .yaml / .yml / .json / .txt。逻辑对齐 Python 版的 import_external_playlist。</summary>
public static class ImportService
{
    public const string DefaultRequester = "导入";

    public static List<Song> ReadSongsFromFile(string path)
    {
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("文件不存在", path);
        }

        var ext = Path.GetExtension(path).ToLowerInvariant();
        var songs = ext switch
        {
            ".yaml" or ".yml" => ReadYaml(path),
            ".json" => ReadJson(path),
            ".txt" => ReadText(path),
            _ => throw new NotSupportedException("仅支持 .yaml / .yml / .json / .txt"),
        };

        return songs.Select(SongService.Normalize).ToList();
    }

    private static List<Song> ReadYaml(string path)
    {
        var file = YamlStore.Load<SongFile>(path);
        if (file?.Songs is { Count: > 0 })
        {
            return file.Songs;
        }
        return YamlStore.LoadList<Song>(path) ?? new List<Song>();
    }

    private static List<Song> ReadJson(string path)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(path, Encoding.UTF8));
        var root = doc.RootElement;
        if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("songs", out var arr))
        {
            root = arr;
        }
        if (root.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidDataException("JSON 里没有找到 songs 列表");
        }

        var songs = new List<Song>();
        foreach (var item in root.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object)
            {
                continue;
            }
            var name = GetString(item, "song_name", "songname", "name");
            if (string.IsNullOrWhiteSpace(name))
            {
                continue;
            }
            songs.Add(new Song
            {
                SongName = name.Trim(),
                Artist = (GetString(item, "artist", "singer") ?? "").Trim(),
                Url = FirstUrl(item),
                RequestedBy = (GetString(item, "requested_by", "requester") ?? DefaultRequester).Trim(),
            });
        }
        return songs;
    }

    private static string FirstUrl(JsonElement item)
    {
        foreach (var key in new[] { "url", "url_list" })
        {
            if (!item.TryGetProperty(key, out var value))
            {
                continue;
            }
            if (value.ValueKind == JsonValueKind.String)
            {
                return value.GetString() ?? "";
            }
            if (value.ValueKind == JsonValueKind.Array && value.GetArrayLength() > 0 &&
                value[0].ValueKind == JsonValueKind.String)
            {
                return value[0].GetString() ?? "";
            }
        }
        return "";
    }

    private static string GetString(JsonElement item, params string[] keys)
    {
        foreach (var key in keys)
        {
            if (item.TryGetProperty(key, out var value) && value.ValueKind == JsonValueKind.String)
            {
                return value.GetString();
            }
        }
        return null;
    }

    private static List<Song> ReadText(string path)
    {
        var songs = new List<Song>();
        foreach (var raw in File.ReadAllLines(path, Encoding.UTF8))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith("#"))
            {
                continue;
            }
            var name = line;
            var artist = "";
            var separator = line.IndexOf(" - ", StringComparison.Ordinal);
            if (separator >= 0)
            {
                name = line[..separator].Trim();
                artist = line[(separator + 3)..].Trim();
            }
            if (name.Length == 0)
            {
                continue;
            }
            songs.Add(new Song { SongName = name, Artist = artist, RequestedBy = DefaultRequester });
        }
        return songs;
    }

    /// <summary>导入为新歌单，返回 (歌单ID, 数量)。</summary>
    public static (string PlaylistId, int Count) ImportAsNewPlaylist(string path, string name)
    {
        var songs = ReadSongsFromFile(path);
        if (songs.Count == 0)
        {
            throw new InvalidDataException("文件里没有可用歌曲");
        }
        var playlistId = PlaylistService.CreatePlaylist(name, $"从文件导入: {Path.GetFileName(path)}");
        SongService.SaveSongs(playlistId, songs);
        return (playlistId, songs.Count);
    }

    /// <summary>按「歌名+歌手」去重后合并进已有歌单，返回新增数量。</summary>
    public static int MergeIntoPlaylist(string path, string playlistId)
    {
        var incoming = ReadSongsFromFile(path);
        var songs = SongService.LoadSongs(playlistId);
        var existing = songs.Select(DedupKey).ToHashSet();

        var added = 0;
        foreach (var song in incoming)
        {
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

    private static string DedupKey(Song song)
        => $"{(song.SongName ?? "").Trim().ToLowerInvariant()}\u0001{(song.Artist ?? "").Trim().ToLowerInvariant()}";
}
