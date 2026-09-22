using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class AutoJumpTests
{
    [Fact]
    public void PlaceholdersAreUrlEncoded()
    {
        var song = new Song { SongName = "晴天", Artist = "周杰伦" };
        var url = AutoJumpService.ExpandUrl("https://x/?q={query}&s={song}&a={artist}", song);
        var expected =
            "https://x/?q=" + Uri.EscapeDataString("晴天 周杰伦") +
            "&s=" + Uri.EscapeDataString("晴天") +
            "&a=" + Uri.EscapeDataString("周杰伦");
        Assert.Equal(expected, url);
    }

    [Fact]
    public void EmptyTemplateReturnsEmpty()
        => Assert.Equal(string.Empty, AutoJumpService.ExpandUrl(string.Empty, new Song()));

    [Fact]
    public void SongUrlWinsByDefault()
    {
        var config = new AutoJumpSettings { Enabled = true, Mode = "search", PreferSearch = false };
        var song = new Song { SongName = "晴天", Artist = "周杰伦", Url = "https://y.qq.com/song/x" };
        Assert.Equal("https://y.qq.com/song/x", AutoJumpService.BuildUrl(song, config));
    }

    [Fact]
    public void PreferSearchIgnoresSongUrl()
    {
        var config = new AutoJumpSettings { Enabled = true, Mode = "search", PreferSearch = true };
        var song = new Song { SongName = "晴天", Artist = "周杰伦", Url = "https://y.qq.com/song/x" };

        var url = AutoJumpService.BuildUrl(song, config);
        Assert.StartsWith("https://search.bilibili.com/all?keyword=", url);
        Assert.Contains(Uri.EscapeDataString("晴天 周杰伦"), url);
    }

    [Fact]
    public void CustomPlaceholderExpands()
    {
        var config = new AutoJumpSettings
        {
            Enabled = true,
            Mode = "custom",
            CustomUrl = "https://search.bilibili.com/all?keyword={query}",
            PreferSearch = true,
        };
        var song = new Song { SongName = "晴天", Artist = "周杰伦", Url = "https://x" };

        Assert.Equal(
            "https://search.bilibili.com/all?keyword=" + Uri.EscapeDataString("晴天 周杰伦"),
            AutoJumpService.BuildUrl(song, config));
    }

    [Fact]
    public void SearchModeNeedsSongName()
    {
        var config = new AutoJumpSettings { Enabled = true, Mode = "search" };
        Assert.Null(AutoJumpService.BuildUrl(new Song { SongName = "", Artist = "" }, config));
    }
}
