using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed partial class PlaylistsPage : Page
{
    private readonly ObservableCollection<PlaylistRow> _rows = new();

    public PlaylistsPage()
    {
        InitializeComponent();
        PlaylistList.ItemsSource = _rows;
        Loaded += (_, _) => Load();
    }

    private string? CurrentId => ConfigService.GetCurrentPlaylistId();

    private void Load()
    {
        var current = CurrentId;
        _rows.Clear();
        foreach (var kv in ConfigService.GetPlaylists())
        {
            var entry = kv.Value;
            var marker = kv.Key == current ? "（当前）" : "";
            _rows.Add(new PlaylistRow
            {
                Id = kv.Key,
                DisplayName = $"{entry?.Name ?? kv.Key}{marker}",
                SubText = $"{kv.Key} · {entry?.SongCount ?? 0} 首",
            });
        }
        HeaderText.Text = $"歌单管理（{_rows.Count} 个）";
    }

    private void Refresh_Click(object sender, RoutedEventArgs e) => Load();

    private async void Switch_Click(object sender, RoutedEventArgs e)
    {
        if (PlaylistList.SelectedItem is not PlaylistRow row)
        {
            await ShowMessage("请先选择一个歌单");
            return;
        }
        if (row.Id == CurrentId)
        {
            await ShowMessage("已经是当前歌单");
            return;
        }
        ConfigService.SetCurrentPlaylist(row.Id);
        HistoryService.RecordOperation("切换歌单", $"切换到 '{row.DisplayName}'", playlistId: row.Id);
        Load();
    }

    private async void New_Click(object sender, RoutedEventArgs e)
    {
        var nameBox = new TextBox { Header = "歌单名称", Width = 340 };
        var descBox = new TextBox { Header = "描述（可空）", Width = 340 };
        var panel = new StackPanel { Spacing = 10 };
        panel.Children.Add(nameBox);
        panel.Children.Add(descBox);

        var dialog = new ContentDialog
        {
            Title = "新建歌单",
            Content = panel,
            PrimaryButtonText = "创建",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
            IsPrimaryButtonEnabled = false,
        };
        nameBox.TextChanged += (_, _) => dialog.IsPrimaryButtonEnabled = !string.IsNullOrWhiteSpace(nameBox.Text);
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var name = nameBox.Text.Trim();
        var playlistId = PlaylistService.CreatePlaylist(name, descBox.Text.Trim());
        HistoryService.RecordOperation("创建歌单", $"歌单: {name}", playlistId: playlistId);
        Load();
    }

    private async void Rename_Click(object sender, RoutedEventArgs e)
    {
        if (PlaylistList.SelectedItem is not PlaylistRow row)
        {
            await ShowMessage("请先选择一个歌单");
            return;
        }
        var entry = ConfigService.GetPlaylist(row.Id);
        var nameBox = new TextBox { Header = "新的名称", Text = entry?.Name ?? "", Width = 340 };
        var descBox = new TextBox { Header = "描述（可空）", Text = entry?.Description ?? "", Width = 340 };
        var panel = new StackPanel { Spacing = 10 };
        panel.Children.Add(nameBox);
        panel.Children.Add(descBox);

        var dialog = new ContentDialog
        {
            Title = "重命名歌单",
            Content = panel,
            PrimaryButtonText = "保存",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }
        if (string.IsNullOrWhiteSpace(nameBox.Text))
        {
            return;
        }

        PlaylistService.RenamePlaylist(row.Id, nameBox.Text.Trim(), descBox.Text.Trim());
        HistoryService.RecordOperation("重命名歌单", $"歌单: {row.Id} -> {nameBox.Text.Trim()}", playlistId: row.Id);
        Load();
    }

    private async void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (PlaylistList.SelectedItem is not PlaylistRow row)
        {
            await ShowMessage("请先选择一个歌单");
            return;
        }
        var confirm = new ContentDialog
        {
            Title = "删除歌单",
            Content = $"确定删除「{row.DisplayName}」吗？其数据目录会被一并删除，且不可恢复。",
            PrimaryButtonText = "删除",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var (ok, message) = PlaylistService.DeletePlaylist(row.Id);
        if (!ok)
        {
            await ShowMessage(message);
            return;
        }
        HistoryService.RecordOperation("删除歌单", $"歌单: {row.Id}");
        Load();
    }

    private void BackupOne_Click(object sender, RoutedEventArgs e)
    {
        var target = (PlaylistList.SelectedItem as PlaylistRow)?.Id ?? CurrentId;
        if (string.IsNullOrEmpty(target))
        {
            BackupInfo.Text = "没有可备份的歌单";
            return;
        }
        try
        {
            var path = BackupService.BackupPlaylist(target);
            BackupInfo.Text = $"已备份: {path}";
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"备份失败：{ex.Message}";
        }
    }

    private void BackupAll_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var path = BackupService.BackupAll();
            BackupInfo.Text = $"已备份全部: {path}";
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"备份失败：{ex.Message}";
        }
    }

    private async Task ShowMessage(string message)
    {
        var dialog = new ContentDialog
        {
            Title = "提示",
            Content = message,
            CloseButtonText = "好",
            XamlRoot = XamlRoot,
        };
        await dialog.ShowAsync();
    }
}
