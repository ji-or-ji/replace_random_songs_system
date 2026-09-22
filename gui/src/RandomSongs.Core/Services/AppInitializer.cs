using System.IO;
using System.Linq;

namespace RandomSongs.Core;

/// <summary>首次运行时的初始化：建目录、写模板、创建含示例数据的默认歌单。</summary>
public static class AppInitializer
{
    public static readonly string[] ExampleRequesters = { "阿澈", "小满", "林深", "白露" };

    private static readonly (string Song, string Artist, string Requester)[] ExampleSongs =
    {
        ("夜曲", "周杰伦", "阿澈"),
        ("晴天", "周杰伦", "小满"),
        ("平凡之路", "朴树", "林深"),
        ("起风了", "买辣椒也用券", "白露"),
        ("稻香", "周杰伦", "阿澈"),
    };

    public static void Initialize(bool quiet = false)
    {
        Directory.CreateDirectory(AppPaths.DataRoot);
        Directory.CreateDirectory(AppPaths.GlobalDir);
        Directory.CreateDirectory(AppPaths.PlaylistRoot);
        Directory.CreateDirectory(AppPaths.TemplateDir);

        var cfg = ConfigService.Load();
        if (!ConfigService.Exists() || cfg.Playlists.Count == 0)
        {
            if (!quiet)
            {
                Console.WriteLine("首次运行：创建默认歌单与示例数据...");
            }
            SeedDefaultPlaylist();
        }

        if (!File.Exists(AppPaths.SystemStatsFile))
        {
            YamlStore.Save(AppPaths.SystemStatsFile, new SystemStats());
        }

        cfg = ConfigService.Load();
        if (string.IsNullOrEmpty(cfg.InitializedAt))
        {
            cfg.InitializedAt = SongService.Now();
            ConfigService.Save(cfg);
        }

        ConfigService.GetCurrentPlaylistId();
    }

    private static void SeedDefaultPlaylist()
    {
        var requesters = ExampleRequesters.Select(name => new Requester { Name = name }).ToList();
        var now = SongService.Now();
        var songs = ExampleSongs
            .Select(t => SongService.Normalize(new Song
            {
                SongName = t.Song,
                Artist = t.Artist,
                Url = "",
                RequestedBy = t.Requester,
                CreatedAt = now,
                LastModified = now,
            }))
            .ToList();

        PlaylistService.RegisterPlaylist("default", "默认歌单", "主歌单（含示例歌曲）");
        PlaylistService.EnsurePlaylistFiles("default", songs, requesters);
        ConfigService.UpdateSongCount("default", songs.Count);
        ConfigService.SetCurrentPlaylist("default");
    }
}
