using System.Linq;
using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class PlaylistAdminTests : TempDataTest
{
    [Fact]
    public void RenameKeepsIdAndFolder()
    {
        Assert.True(PlaylistService.RenamePlaylist("default", "新名字", "新描述"));
        var entry = ConfigService.GetPlaylist("default");
        Assert.NotNull(entry);
        Assert.Equal("新名字", entry!.Name);
        Assert.Equal("新描述", entry.Description);
        Assert.Contains(ConfigService.GetPlaylists(), kv => kv.Key == "default");
        Assert.True(Directory.Exists(AppPaths.PlaylistDir("default")));
    }

    [Fact]
    public void CannotDeleteCurrentOrLast()
    {
        var (ok, message) = PlaylistService.DeletePlaylist("default");
        Assert.False(ok);
        Assert.False(string.IsNullOrEmpty(message));
        Assert.Contains(ConfigService.GetPlaylists(), kv => kv.Key == "default");
    }

    [Fact]
    public void DeleteNonCurrentRemovesEntryAndFolder()
    {
        var id = PlaylistService.CreatePlaylist("临时歌单");
        Assert.True(Directory.Exists(AppPaths.PlaylistDir(id)));

        // 先切到 default，保证临时歌单不是当前
        ConfigService.SetCurrentPlaylist("default");
        var (ok, _) = PlaylistService.DeletePlaylist(id);

        Assert.True(ok);
        Assert.DoesNotContain(ConfigService.GetPlaylists(), kv => kv.Key == id);
        Assert.False(Directory.Exists(AppPaths.PlaylistDir(id)));
    }

    [Fact]
    public void BackupCreatesZipsInsideTempTree()
    {
        var all = BackupService.BackupAll();
        Assert.True(File.Exists(all));
        Assert.StartsWith(TempDir, all);

        var one = BackupService.BackupPlaylist("default");
        Assert.True(File.Exists(one));
        Assert.StartsWith(TempDir, one);
    }

    [Fact]
    public void HistoryReadBack()
    {
        var song = SongService.LoadSongs("default")[0];
        HistoryService.RecordPlay(song, "default");

        var playLines = HistoryService.ReadHistory(HistoryScope.PlaylistPlay, "default");
        Assert.NotEmpty(playLines);
        Assert.Contains(playLines, line => line.Contains("播放"));
    }
}
