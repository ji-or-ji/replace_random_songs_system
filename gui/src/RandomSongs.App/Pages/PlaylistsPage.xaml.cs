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

    private async void Restore_Click(object sender, RoutedEventArgs e)
    {
        var picker = new Windows.Storage.Pickers.FileOpenPicker();
        if (App.Instance is not null)
        {
            var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Instance);
            WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
        }
        picker.SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add(".zip");

        var file = await picker.PickSingleFileAsync();
        if (file is null)
        {
            return;
        }

        BackupInfo info;
        try
        {
            info = BackupService.Inspect(file.Path);
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"读取备份失败：{ex.Message}";
            return;
        }
        if (info.Kind == BackupKind.Unknown)
        {
            BackupInfo.Text = "无法识别的备份文件（既不是整库备份，也不是单歌单备份）";
            return;
        }

        var what = info.Kind == BackupKind.Full
            ? $"整库备份（{info.EntryCount} 个文件）"
            : $"单歌单备份（歌单 ID: {info.PlaylistId}，{info.EntryCount} 个文件）";
        var effect = info.Kind == BackupKind.Full
            ? "确定要用这份整库备份【覆盖当前全部数据】吗？现有数据会被替换。（恢复前会自动再做一次安全备份）"
            : $"确定要用这份备份【覆盖歌单「{info.PlaylistId}」】吗？（覆盖前会自动再备份一次）";

        var confirm = new ContentDialog
        {
            Title = "从备份恢复",
            Content = $"{what}\n\n{effect}",
            PrimaryButtonText = "恢复",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        try
        {
            if (info.Kind == BackupKind.Full)
            {
                var safety = BackupService.RestoreAll(file.Path);
                HistoryService.RecordOperation(
                    "从备份恢复", $"整库: {file.Name}（恢复前安全备份: {System.IO.Path.GetFileName(safety)}）");
                BackupInfo.Text = $"已恢复整库。恢复前的数据已备份到：{safety}";
            }
            else
            {
                var (playlistId, files) = BackupService.RestorePlaylist(file.Path);
                HistoryService.RecordOperation("从备份恢复", $"歌单: {playlistId}, 文件: {files}", playlistId: playlistId);
                BackupInfo.Text = $"已恢复歌单「{playlistId}」：{files} 个文件";
            }
            Load();
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"恢复失败：{ex.Message}";
        }
    }

    private async void ImportFile_Click(object sender, RoutedEventArgs e)
    {
        var picker = new Windows.Storage.Pickers.FileOpenPicker();
        if (App.Instance is not null)
        {
            var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Instance);
            WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
        }
        picker.SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.DocumentsLibrary;
        foreach (var ext in new[] { ".yaml", ".yml", ".json", ".txt" })
        {
            picker.FileTypeFilter.Add(ext);
        }

        var file = await picker.PickSingleFileAsync();
        if (file is null)
        {
            return;
        }

        var nameBox = new TextBox
        {
            Header = "新歌单名称",
            Text = System.IO.Path.GetFileNameWithoutExtension(file.Name),
            Width = 340,
        };
        var mergeCheck = new CheckBox { Content = "合并进当前歌单（不勾选则新建歌单）" };
        var panel = new StackPanel { Spacing = 10 };
        panel.Children.Add(nameBox);
        panel.Children.Add(mergeCheck);

        var dialog = new ContentDialog
        {
            Title = "从文件导入",
            Content = panel,
            PrimaryButtonText = "导入",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        try
        {
            if (mergeCheck.IsChecked == true)
            {
                var target = CurrentId;
                if (string.IsNullOrEmpty(target))
                {
                    BackupInfo.Text = "没有当前歌单可合并";
                    return;
                }
                var added = ImportService.MergeIntoPlaylist(file.Path, target);
                HistoryService.RecordOperation("导入歌单", $"文件: {file.Name}, 合并新增: {added}", playlistId: target);
                BackupInfo.Text = $"已合并进当前歌单：新增 {added} 首";
            }
            else
            {
                if (string.IsNullOrWhiteSpace(nameBox.Text))
                {
                    BackupInfo.Text = "歌单名称不能为空";
                    return;
                }
                var (playlistId, count) = ImportService.ImportAsNewPlaylist(file.Path, nameBox.Text.Trim());
                HistoryService.RecordOperation("导入歌单", $"文件: {file.Name}, 歌曲数: {count}", playlistId: playlistId);
                BackupInfo.Text = $"已导入为新歌单：{count} 首";
                Load();
            }
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"导入失败：{ex.Message}";
        }
    }

    private async void ImportFolder_Click(object sender, RoutedEventArgs e)
    {
        var picker = new Windows.Storage.Pickers.FolderPicker();
        if (App.Instance is not null)
        {
            var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.Instance);
            WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
        }
        picker.SuggestedStartLocation = Windows.Storage.Pickers.PickerLocationId.MusicLibrary;
        picker.FileTypeFilter.Add("*");

        var folder = await picker.PickSingleFolderAsync();
        if (folder is null)
        {
            return;
        }

        var known = FolderImportService.CollectKnownArtists();
        var rows = new ObservableCollection<ParsedFileRow>();
        var parsed = new List<FolderImportService.ParsedFile>();

        var nameBox = new TextBox { Header = "新歌单名称", Text = folder.Name, Width = 460 };
        var mergeCheck = new CheckBox { Content = "合并进当前歌单（不勾选则新建歌单）" };
        var recursiveCheck = new CheckBox { Content = "包含子文件夹" };
        var orderCombo = new ComboBox { Header = "文件名顺序", Width = 200, HorizontalAlignment = HorizontalAlignment.Left };
        orderCombo.Items.Add("歌手 - 歌名");
        orderCombo.Items.Add("歌名 - 歌手");
        orderCombo.SelectedIndex = 0;
        var summary = new TextBlock { Opacity = 0.7, TextWrapping = TextWrapping.Wrap };
        var preview = new ListView
        {
            ItemsSource = rows,
            MaxHeight = 260,
            SelectionMode = ListViewSelectionMode.None,
            ItemTemplate = (DataTemplate)Resources["ParsedRowTemplate"],
        };

        void Rescan()
        {
            var artistFirst = orderCombo.SelectedIndex == 0;
            parsed = FolderImportService.ScanFolder(
                folder.Path, recursiveCheck.IsChecked == true, artistFirst, known);
            rows.Clear();
            foreach (var item in parsed)
            {
                rows.Add(new ParsedFileRow
                {
                    SongName = item.SongName,
                    Artist = string.IsNullOrEmpty(item.Artist) ? "（未识别出歌手）" : item.Artist,
                    NoteText = string.IsNullOrEmpty(item.Note) ? item.FileName : $"{item.FileName}  ·  {item.Note}",
                });
            }
            var unknown = parsed.Count(p => string.IsNullOrEmpty(p.Artist));
            summary.Text = $"共 {parsed.Count} 个音频文件" + (unknown > 0 ? $"，其中 {unknown} 个未识别出歌手" : "");
        }

        recursiveCheck.Checked += (_, _) => Rescan();
        recursiveCheck.Unchecked += (_, _) => Rescan();
        orderCombo.SelectionChanged += (_, _) => Rescan();
        Rescan();

        var panel = new StackPanel { Spacing = 10, Width = 470 };
        panel.Children.Add(nameBox);
        panel.Children.Add(mergeCheck);
        panel.Children.Add(recursiveCheck);
        panel.Children.Add(orderCombo);
        panel.Children.Add(summary);
        panel.Children.Add(preview);

        var dialog = new ContentDialog
        {
            Title = $"从文件夹导入：{folder.Name}",
            Content = panel,
            PrimaryButtonText = "导入",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        if (parsed.Count == 0)
        {
            BackupInfo.Text = "该文件夹里没有音频文件";
            return;
        }

        try
        {
            if (mergeCheck.IsChecked == true)
            {
                var target = CurrentId;
                if (string.IsNullOrEmpty(target))
                {
                    BackupInfo.Text = "没有当前歌单可合并";
                    return;
                }
                var added = FolderImportService.ImportIntoPlaylist(target, parsed);
                HistoryService.RecordOperation("文件夹导入", $"目录: {folder.Path}, 新增: {added}", playlistId: target);
                BackupInfo.Text = $"已合并进当前歌单：新增 {added} 首（共解析 {parsed.Count} 个文件）";
            }
            else
            {
                var name = string.IsNullOrWhiteSpace(nameBox.Text) ? folder.Name : nameBox.Text.Trim();
                var (playlistId, count) = FolderImportService.ImportAsNewPlaylist(name, folder.Path, parsed);
                HistoryService.RecordOperation("文件夹导入", $"目录: {folder.Path}, 歌曲数: {count}", playlistId: playlistId);
                BackupInfo.Text = $"已导入为新歌单：{count} 首";
                Load();
            }
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"导入失败：{ex.Message}";
        }
    }

    private async void ImportQq_Click(object sender, RoutedEventArgs e)
    {
        var idBox = new TextBox { Header = "QQ 歌单 ID 或分享链接", Width = 360 };
        var nameBox = new TextBox { Header = "新歌单名称", Text = "QQ歌单", Width = 360 };
        var panel = new StackPanel { Spacing = 10 };
        panel.Children.Add(idBox);
        panel.Children.Add(nameBox);

        var dialog = new ContentDialog
        {
            Title = "从 QQ 歌单导入",
            Content = panel,
            PrimaryButtonText = "导入",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }
        if (string.IsNullOrWhiteSpace(idBox.Text))
        {
            BackupInfo.Text = "请填写 QQ 歌单 ID 或链接";
            return;
        }

        BackupInfo.Text = "正在拉取...";
        try
        {
            var (playlistId, count) = await QqPlaylistService.ImportAsync(
                idBox.Text.Trim(),
                newPlaylistName: string.IsNullOrWhiteSpace(nameBox.Text) ? null : nameBox.Text.Trim());
            var name = ConfigService.GetPlaylist(playlistId)?.Name ?? playlistId;
            BackupInfo.Text = $"已导入为新歌单「{name}」：{count} 首";
            Load();
        }
        catch (Exception ex)
        {
            BackupInfo.Text = $"导入失败：{ex.Message}";
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
