namespace RandomSongs.App.Pages;

/// <summary>界面用的简单行模型（ListView 绑定）。</summary>
public sealed class SimpleTextRow
{
    public string Text { get; set; } = "";
}

public sealed class SongSearchRow
{
    public string SongName { get; set; } = "";
    public string SubText { get; set; } = "";
}

public sealed class PlaylistRow
{
    public string Id { get; set; } = "";
    public string DisplayName { get; set; } = "";
    public string SubText { get; set; } = "";
}

public sealed class ParsedFileRow
{
    public string SongName { get; set; } = "";
    public string Artist { get; set; } = "";
    public string NoteText { get; set; } = "";
}
