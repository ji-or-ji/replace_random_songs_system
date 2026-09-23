using RandomSongs.Core;
using Xunit;

namespace RandomSongs.Core.Tests;

public class FolderImportTests : TempDataTest
{
    private static HashSet<string> Known(params string[] names)
        => new(names, StringComparer.OrdinalIgnoreCase);

    [Theory]
    [InlineData("周杰伦 - 晴天", true, "晴天", "周杰伦")]
    [InlineData("晴天 - 周杰伦", false, "晴天", "周杰伦")]
    [InlineData("01. 周杰伦 - 晴天", true, "晴天", "周杰伦")]
    [InlineData("01 - 周杰伦 - 晴天", true, "晴天", "周杰伦")]
    [InlineData("周杰伦-晴天", true, "晴天", "周杰伦")]
    [InlineData("周杰伦《晴天》", true, "晴天", "周杰伦")]
    [InlineData("[周杰伦] 晴天", true, "晴天", "周杰伦")]
    [InlineData("晴天 (周杰伦)", true, "晴天", "周杰伦")]
    [InlineData("晴天", true, "晴天", "")]
    [InlineData("2002年的第一场雪", true, "2002年的第一场雪", "")]
    public void ParseCommonFormats(string raw, bool artistFirst, string song, string artist)
    {
        var (parsedSong, parsedArtist, _) = FolderImportService.ParseName(raw, artistFirst, Known());
        Assert.Equal(song, parsedSong);
        Assert.Equal(artist, parsedArtist);
    }

    [Fact]
    public void KnownArtistCorrectsSwappedOrder()
    {
        var (song, artist, note) = FolderImportService.ParseName("晴天 - 周杰伦", true, Known("周杰伦", "朴树"));
        Assert.Equal("晴天", song);
        Assert.Equal("周杰伦", artist);
        Assert.Equal("已知歌手校正", note);
    }

    [Fact]
    public void OrderToggleFlipsWhenNoKnownArtist()
    {
        var (s1, a1, _) = FolderImportService.ParseName("甲 - 乙", true, Known());
        Assert.Equal("乙", s1);
        Assert.Equal("甲", a1);

        var (s2, a2, _) = FolderImportService.ParseName("甲 - 乙", false, Known());
        Assert.Equal("甲", s2);
        Assert.Equal("乙", a2);
    }

    [Fact]
    public void ScanFolderOnlyAudioFiles()
    {
        var folder = Path.Combine(TempDir, "music");
        Directory.CreateDirectory(folder);
        File.WriteAllText(Path.Combine(folder, "周杰伦 - 晴天.mp3"), "");
        File.WriteAllText(Path.Combine(folder, "周杰伦 - 晴天.lrc"), "");
        File.WriteAllText(Path.Combine(folder, "朴树 - 平凡之路.flac"), "");

        var files = FolderImportService.ScanFolder(folder, recursive: false, artistFirst: true, knownArtists: Known());
        Assert.Equal(2, files.Count);
        Assert.Contains(files, f => f.SongName == "晴天" && f.Artist == "周杰伦");
    }

    [Fact]
    public void ImportIntoPlaylistStoresLocalPath()
    {
        var files = new List<FolderImportService.ParsedFile>
        {
            new() { FilePath = @"C:\music\a.mp3", FileName = "a.mp3", SongName = "甲", Artist = "乙" },
        };
        var added = FolderImportService.ImportIntoPlaylist("default", files);
        Assert.Equal(1, added);

        var stored = SongService.LoadSongs("default").First(s => s.SongName == "甲");
        Assert.Equal(@"C:\music\a.mp3", stored.LocalPath);
    }

    [Fact]
    public void HasLocalFileChecksExistence()
    {
        var missing = new Song { SongName = "x", LocalPath = @"C:\nope\none.mp3" };
        Assert.False(LocalPlaybackService.HasLocalFile(missing));

        var realPath = Path.Combine(TempDir, "song.mp3");
        File.WriteAllText(realPath, "");
        Assert.True(LocalPlaybackService.HasLocalFile(new Song { SongName = "x", LocalPath = realPath }));
    }
}
