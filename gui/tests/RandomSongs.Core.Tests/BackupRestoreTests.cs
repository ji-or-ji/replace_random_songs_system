using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class BackupRestoreTests : TempDataTest
{
    [Fact]
    public void InspectDetectsKinds()
    {
        var full = BackupService.BackupAll();
        var fullInfo = BackupService.Inspect(full);
        Assert.Equal(BackupKind.Full, fullInfo.Kind);
        Assert.True(fullInfo.EntryCount > 0);

        var one = BackupService.BackupPlaylist("default");
        var oneInfo = BackupService.Inspect(one);
        Assert.Equal(BackupKind.Playlist, oneInfo.Kind);
        Assert.Equal("default", oneInfo.PlaylistId);
    }

    [Fact]
    public void RepeatedBackupsDoNotOverwriteEachOther()
    {
        var a = BackupService.BackupAll();
        var b = BackupService.BackupAll();
        Assert.NotEqual(a, b);
        Assert.True(File.Exists(a));
        Assert.True(File.Exists(b));
    }

    [Fact]
    public void RestoreAllRollsBackToBackupState()
    {
        // 备份时的状态：5 首
        var archive = BackupService.BackupAll();
        var before = SongService.LoadSongs("default").Count;

        // 之后又加了 2 首
        var songs = SongService.LoadSongs("default");
        songs.Add(SongService.Normalize(new Song { SongName = "临时A", Artist = "X" }));
        songs.Add(SongService.Normalize(new Song { SongName = "临时B", Artist = "Y" }));
        SongService.SaveSongs("default", songs);
        Assert.Equal(before + 2, SongService.LoadSongs("default").Count);

        // 恢复整库
        var safety = BackupService.RestoreAll(archive);

        Assert.True(File.Exists(safety)); // 恢复前自动做了安全备份
        Assert.NotEqual(archive, safety); // 且不会覆盖原始备份

        var after = SongService.LoadSongs("default");
        Assert.Equal(before, after.Count);
        Assert.DoesNotContain(after, s => s.SongName == "临时A");
        Assert.DoesNotContain(after, s => s.SongName == "临时B");
    }

    [Fact]
    public void RestoreAllRejectsPlaylistBackup()
    {
        var one = BackupService.BackupPlaylist("default");
        Assert.Throws<InvalidOperationException>(() => BackupService.RestoreAll(one));
    }

    [Fact]
    public void RestorePlaylistRestoresSongs()
    {
        var archive = BackupService.BackupPlaylist("default");
        var before = SongService.LoadSongs("default").Count;

        // 破坏：清空该歌单歌曲
        SongService.SaveSongs("default", new List<Song>());
        Assert.Empty(SongService.LoadSongs("default"));

        var (playlistId, files) = BackupService.RestorePlaylist(archive);

        Assert.Equal("default", playlistId);
        Assert.True(files > 0);
        Assert.Equal(before, SongService.LoadSongs("default").Count);
    }
}
