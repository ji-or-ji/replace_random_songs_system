using System.Text;
using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class ImportTests : TempDataTest
{
    private string WriteTemp(string name, string content)
    {
        var path = Path.Combine(TempDir, name);
        File.WriteAllText(path, content, new UTF8Encoding(false));
        return path;
    }

    [Fact]
    public void ReadYamlMapping()
    {
        var path = WriteTemp("a.yaml", "songs:\n- song_name: 知我\n  artist: 某某\n  requested_by: 阿澈\n");
        var songs = ImportService.ReadSongsFromFile(path);
        Assert.Single(songs);
        Assert.Equal("知我", songs[0].SongName);
        Assert.Equal("阿澈", songs[0].RequestedBy);
    }

    [Fact]
    public void ReadYamlBareList()
    {
        var path = WriteTemp("b.yaml", "- song_name: 甲\n  artist: 乙\n- song_name: 丙\n");
        var songs = ImportService.ReadSongsFromFile(path);
        Assert.Equal(2, songs.Count);
        Assert.Equal("甲", songs[0].SongName);
    }

    [Fact]
    public void ReadJson()
    {
        var path = WriteTemp(
            "c.json",
            "{\"songs\":[{\"song_name\":\"晴天\",\"artist\":\"周杰伦\",\"url_list\":[\"http://a\"]}]}");
        var songs = ImportService.ReadSongsFromFile(path);
        Assert.Single(songs);
        Assert.Equal("晴天", songs[0].SongName);
        Assert.Equal("http://a", songs[0].Url);
    }

    [Fact]
    public void ReadTxt()
    {
        var path = WriteTemp("d.txt", "# comment\n晴天 - 周杰伦\n平凡之路\n");
        var songs = ImportService.ReadSongsFromFile(path);
        Assert.Equal(2, songs.Count);
        Assert.Equal("晴天", songs[0].SongName);
        Assert.Equal("周杰伦", songs[0].Artist);
        Assert.Equal("平凡之路", songs[1].SongName);
    }

    [Fact]
    public void ImportAsNewPlaylistThenMerge()
    {
        var path = WriteTemp("e.txt", "晴天 - 周杰伦\n新歌 - 某手\n");
        var (playlistId, count) = ImportService.ImportAsNewPlaylist(path, "导入测试");
        Assert.Equal(2, count);
        Assert.Equal(2, SongService.LoadSongs(playlistId).Count);

        // 再合并同一文件：都已在 → 0 新增
        Assert.Equal(0, ImportService.MergeIntoPlaylist(path, playlistId));

        // 文件多一首后：1 新增
        var path2 = WriteTemp("f.txt", "晴天 - 周杰伦\n新歌 - 某手\n又一首 - 某丙\n");
        Assert.Equal(1, ImportService.MergeIntoPlaylist(path2, playlistId));
        Assert.Equal(3, SongService.LoadSongs(playlistId).Count);
    }
}
