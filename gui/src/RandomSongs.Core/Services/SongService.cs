using System.Linq;

namespace RandomSongs.Core;

/// <summary>歌曲数据的读写、规范化与统计。</summary>
public static class SongService
{
    // 注意：时间用斜杠格式（yyyy/MM/dd HH:mm:ss）。这种写法在 YAML 里不是时间戳类型，
    // 因此 C# 与 Python(PyYAML) 都会读成字符串；Python 侧的解析同时接受斜杠与短横两种格式。
    public static string Now() => DateTime.Now.ToString("yyyy/MM/dd HH:mm:ss");

    public static string NewSongId() => Guid.NewGuid().ToString();

    public static Song Normalize(Song song)
    {
        song ??= new Song();
        song.SongName ??= "";
        song.Artist ??= "";
        song.Url ??= "";
        song.LocalPath ??= "";
        song.RequestedBy ??= "";
        if (string.IsNullOrEmpty(song.Id))
        {
            song.Id = NewSongId();
        }
        song.CreatedAt ??= Now();
        song.LastModified ??= song.CreatedAt;
        return song;
    }

    /// <summary>加载歌曲并自动补齐缺失字段；有修复时回写。</summary>
    public static List<Song> LoadSongs(string playlistId)
    {
        if (string.IsNullOrEmpty(playlistId))
        {
            return new List<Song>();
        }

        var file = YamlStore.Load<SongFile>(AppPaths.SongsFile(playlistId));
        var raw = file?.Songs ?? new List<Song>();

        var healed = raw.Any(s => string.IsNullOrEmpty(s?.Id) || s?.CreatedAt == null);
        var songs = raw.Select(Normalize).ToList();

        if (healed)
        {
            SaveSongs(playlistId, songs);
        }
        else
        {
            ConfigService.UpdateSongCount(playlistId, songs.Count);
        }
        return songs;
    }

    public static bool SaveSongs(string playlistId, List<Song> songs)
    {
        if (string.IsNullOrEmpty(playlistId))
        {
            return false;
        }
        YamlStore.Save(AppPaths.SongsFile(playlistId), new SongFile { Songs = songs });
        ConfigService.UpdateSongCount(playlistId, songs.Count);
        return true;
    }

    public static List<Song> FilterValid(IEnumerable<Song> songs)
        => (songs ?? Enumerable.Empty<Song>())
            .Where(s => s != null && !string.IsNullOrWhiteSpace(s.SongName))
            .ToList();

    public static Song FindById(IEnumerable<Song> songs, string id)
        => (songs ?? Enumerable.Empty<Song>()).FirstOrDefault(s => s != null && s.Id == id);

    public sealed class Statistics
    {
        public int TotalSongs { get; init; }
        public int ValidSongs { get; init; }
        public int InvalidSongs { get; init; }
        public List<KeyValuePair<string, int>> Requesters { get; init; } = new();
    }

    public static Statistics GetStatistics(IEnumerable<Song> songs)
    {
        var all = songs?.ToList() ?? new List<Song>();
        var valid = FilterValid(all);
        var requesters = valid
            .GroupBy(s => string.IsNullOrEmpty(s.RequestedBy) ? "未知" : s.RequestedBy)
            .Select(g => new KeyValuePair<string, int>(g.Key, g.Count()))
            .OrderByDescending(kv => kv.Value)
            .ThenBy(kv => kv.Key)
            .ToList();
        return new Statistics
        {
            TotalSongs = all.Count,
            ValidSongs = valid.Count,
            InvalidSongs = all.Count - valid.Count,
            Requesters = requesters,
        };
    }
}
