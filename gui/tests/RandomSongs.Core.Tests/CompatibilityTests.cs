using System.Text;
using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

/// <summary>验证能直接读取 Python 版写出的 YAML（互通性）。</summary>
public class CompatibilityTests
{
    [Fact]
    public void ParsesPythonStyleGlobalConfig()
    {
        const string yaml = """
            system_version: '2.1'
            initialized_at: '2026-09-22 17:11:36'
            current_playlist: default
            auto_jump:
              enabled: false
              mode: search
              custom_url: ''
              delay: 3
              prefer_search: false
            qq_sync:
              enabled: true
              playlist_id: ''
              auto_on_start: true
            playlists:
              default:
                name: 默认歌单
                description: 主歌单（含示例歌曲）
                created_at: 2026/09/22
                song_count: 5
                duplicate_prevention:
                  enabled: true
                  mode: time_window
                  time_window_minutes: 60
                  reset_on_all_played: true
                  avoid_immediate_repeat: true
                  last_reset_time: null
                  played_songs: []
            """;

        var dir = Path.Combine(Path.GetTempPath(), "rss_compat_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        var path = Path.Combine(dir, "global_config.yaml");
        File.WriteAllText(path, yaml, new UTF8Encoding(false));

        var config = YamlStore.Load<GlobalConfig>(path);
        Directory.Delete(dir, true);

        Assert.NotNull(config);
        Assert.Equal("default", config!.CurrentPlaylist);
        Assert.Equal("默认歌单", config.Playlists["default"].Name);
        Assert.Equal("主歌单（含示例歌曲）", config.Playlists["default"].Description);
        Assert.Equal(60, config.Playlists["default"].Prevention.TimeWindowMinutes);
        Assert.Equal("time_window", config.Playlists["default"].Prevention.Mode);
    }

    [Fact]
    public void ParsesPythonStyleSongsFile()
    {
        const string yaml = """
            songs:
            - id: 1cb3b4f0-82ab-4e0e-bf6d-e5a23fb33457
              song_name: 夜曲
              artist: 周杰伦
              url: ''
              requested_by: 阿澈
              created_at: '2026-09-22 17:11:36'
              last_modified: '2026-09-22 17:11:36'
            """;

        var dir = Path.Combine(Path.GetTempPath(), "rss_compat_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        var path = Path.Combine(dir, "songs.yaml");
        File.WriteAllText(path, yaml, new UTF8Encoding(false));

        var file = YamlStore.Load<SongFile>(path);
        Directory.Delete(dir, true);

        Assert.NotNull(file);
        Assert.Single(file!.Songs);
        Assert.Equal("夜曲", file.Songs[0].SongName);
        Assert.Equal("周杰伦", file.Songs[0].Artist);
        Assert.Equal("阿澈", file.Songs[0].RequestedBy);
        Assert.Equal(1 + 0, 1);
    }

    [Fact]
    public void RoundTripPreservesChineseAndStructure()
    {
        var dir = Path.Combine(Path.GetTempPath(), "rss_compat_" + Guid.NewGuid().ToString("N"));
        AppPaths.DataRoot = dir;
        AppInitializer.Initialize(quiet: true);

        var before = SongService.LoadSongs("default");
        var after = YamlStore.Load<SongFile>(AppPaths.SongsFile("default"));

        Directory.Delete(dir, true);

        Assert.NotNull(after);
        Assert.Equal(before.Count, after!.Songs.Count);
        Assert.Equal("夜曲", after.Songs[0].SongName);
    }
}
