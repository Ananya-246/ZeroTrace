import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import 'destructive_warning_screen.dart';
import 'overwrite_summary_screen.dart';

/// Step 3 — mirrors ``navigate_and_select()`` (list, sort, folder/file actions).
class FileExplorerScreen extends StatefulWidget {
  const FileExplorerScreen({
    super.key,
    required this.api,
    required this.mode,
    required this.rootPath,
  });

  final ApiClient api;
  final AppMode mode;
  final String rootPath;

  @override
  State<FileExplorerScreen> createState() => _FileExplorerScreenState();
}

class _FileExplorerScreenState extends State<FileExplorerScreen> {
  late String _currentPath;
  Future<BrowseResult>? _browseFuture;

  @override
  void initState() {
    super.initState();
    _currentPath = widget.rootPath;
    _reload();
  }

  void _reload() {
    setState(() {
      _browseFuture = widget.api.browse(_currentPath);
    });
  }

  bool get _atDriveRoot {
    final a = _normalize(_currentPath);
    final b = _normalize(widget.rootPath);
    return a == b;
  }

  String _normalize(String p) {
    var s = p.replaceAll('/', '\\');
    if (s.length > 3 && s.endsWith('\\')) {
      s = s.substring(0, s.length - 1);
    }
    return s.toLowerCase();
  }

  Future<void> _goBack() async {
    if (_atDriveRoot) {
      if (mounted) Navigator.of(context).pop();
      return;
    }
    final res = await widget.api.browse(_currentPath);
    setState(() {
      _currentPath = res.parentPath;
      _reload();
    });
  }

  void _openFolder(String path) {
    setState(() {
      _currentPath = path;
      _reload();
    });
  }

  void _onEntryTap(BrowseEntry e) {
    if (e.isDirectory) {
      _openFolder(e.path);
      return;
    }
    if (!e.isFile) return;

    if (widget.mode == AppMode.overwriteOnly) {
      Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => OverwriteSummaryScreen(
            api: widget.api,
            filePath: e.path,
          ),
        ),
      );
      return;
    }

    // Mode 1 — selecting a file returns it (like CLI digit pick on file).
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DestructiveWarningScreen(
          api: widget.api,
          mode: widget.mode,
          targetPath: e.path,
          targetIsFile: true,
        ),
      ),
    );
  }

  void _wipeThisFolder() {
    if (widget.mode != AppMode.wipeUserData) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DestructiveWarningScreen(
          api: widget.api,
          mode: widget.mode,
          targetPath: _currentPath,
          targetIsFile: false,
        ),
      ),
    );
  }

  void _switchDrive() {
    Navigator.of(context).pop();
  }

  void _cancelAll() {
    Navigator.of(context).popUntil((r) => r.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Browse'),
      ),
      body: Column(
        children: [
          ListTile(
            dense: true,
            leading: const Icon(Icons.folder_open),
            title: const Text('Current path'),
            subtitle: Text(
              _currentPath,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Drive/Root: ${widget.rootPath}\nCurrent Location: $_currentPath',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          const Divider(),
          Expanded(
            child: FutureBuilder<BrowseResult>(
              future: _browseFuture,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snap.hasError) {
                  return Center(child: Text('${snap.error}'));
                }
                final entries = snap.data!.entries;
                return ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                  itemCount: entries.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final e = entries[i];
                    return ListTile(
                      leading: Icon(
                        e.isDirectory ? Icons.folder : Icons.insert_drive_file,
                      ),
                      title: Text(e.name),
                      subtitle: Text(
                        e.path,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      onTap: () => _onEntryTap(e),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              OutlinedButton.icon(
                onPressed: _goBack,
                icon: const Icon(Icons.arrow_upward),
                label: const Text('Back'),
              ),
              if (widget.mode == AppMode.wipeUserData)
                FilledButton.tonalIcon(
                  onPressed: _wipeThisFolder,
                  icon: const Icon(Icons.folder_delete_outlined),
                  label: const Text('Wipe This Folder'),
                ),
              OutlinedButton.icon(
                onPressed: _switchDrive,
                icon: const Icon(Icons.swap_horiz),
                label: const Text('Switch Drive'),
              ),
              TextButton.icon(
                onPressed: _cancelAll,
                icon: const Icon(Icons.close),
                label: const Text('Cancel'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
