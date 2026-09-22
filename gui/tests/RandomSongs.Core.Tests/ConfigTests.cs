using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class ConfigTests : TempDataTest
{
    [Fact]
    public void InitializeCreatesDefaultPlaylist()
    {
        var playlists = ConfigService.GetPlaylists();
        Assert.Contains(playlists, kv => kv.Key == "default");
        Assert.Equal("default", ConfigService.GetCurrentPlaylistId());
        Assert.Equal(5, SongService.LoadSongs("default").Count);
    }

    [Fact]
    public void InitializeIsIdempotent()
    {
        AppInitializer.Initialize(quiet: true);
        AppInitializer.Initialize(quiet: true);
        Assert.Equal(5, SongService.LoadSongs("default").Count);
    }

    [Fact]
    public void SongsRoundTrip()
    {
        var songs = SongService.LoadSongs("default");
        songs.Add(SongService.Normalize(new Song { SongName = "测试曲", Artist = "测试手" }));
        SongService.SaveSongs("default", songs);

        var reloaded = SongService.LoadSongs("default");
        Assert.Equal(6, reloaded.Count);
        Assert.Contains(reloaded, s => s.SongName == "测试曲");
        Assert.All(reloaded, s => Assert.False(string.IsNullOrEmpty(s.Id)));
    }

    [Fact]
    public void PreventionRoundTrip()
    {
        var prevention = ConfigService.GetPrevention("default");
        prevention.TimeWindowMinutes = 30;
        prevention.Mode = "cycle";
        ConfigService.SavePrevention("default", prevention);

        var reloaded = ConfigService.GetPrevention("default");
        Assert.Equal(30, reloaded.TimeWindowMinutes);
        Assert.Equal("cycle", reloaded.Mode);
    }

    [Fact]
    public void Statistics()
    {
        var stats = SongService.GetStatistics(SongService.LoadSongs("default"));
        Assert.Equal(5, stats.ValidSongs);
        Assert.Equal(0, stats.InvalidSongs);
        Assert.Equal(5, stats.Requesters.Sum(kv => kv.Value));
    }
}
