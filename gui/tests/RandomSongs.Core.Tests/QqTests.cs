using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class QqTests : TempDataTest
{
    [Theory]
    [InlineData("123456", "123456")]
    [InlineData("https://y.qq.com/n/ryqq_v2/playlist/98765", "98765")]
    [InlineData("https://c6.y.qq.com/base/fcgi-bin/u?__=VIzuELjHMPmy", null)]
    [InlineData("", null)]
    public void ExtractPlaylistIdFromText(string input, string expected)
        => Assert.Equal(expected, QqPlaylistService.ExtractPlaylistIdFromText(input));

    [Fact]
    public async Task SyncWithoutConfigThrows()
    {
        // 未配置 QQ 歌单 ID 时应立即报错（且不发网络请求）
        await Assert.ThrowsAsync<InvalidOperationException>(() => QqPlaylistService.SyncAsync());
    }
}
