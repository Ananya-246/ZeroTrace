import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import 'destructive_warning_screen.dart';
import 'file_explorer_screen.dart';

/// Step 2 — mirrors ``select_root()`` drive list.
class DriveSelectionScreen extends StatefulWidget {
  const DriveSelectionScreen({super.key, required this.api, required this.mode});

  final ApiClient api;
  final AppMode mode;

  @override
  State<DriveSelectionScreen> createState() => _DriveSelectionScreenState();
}

class _DriveSelectionScreenState extends State<DriveSelectionScreen> {
  late Future<List<String>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.api.listDrives();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Select location — ${widget.mode.title}'),
      ),
      body: FutureBuilder<List<String>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('Could not load drives:\n${snap.error}'),
              ),
            );
          }
          final drives = snap.data ?? [];
          if (drives.isEmpty) {
            return const Center(child: Text('No drives / locations found.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: drives.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, i) {
              final d = drives[i];
              return ListTile(
                leading: const Icon(Icons.storage),
                title: Text(d),
                onTap: () => _onDrive(context, d),
              );
            },
          );
        },
      ),
    );
  }

  void _onDrive(BuildContext context, String drivePath) {
    if (widget.mode == AppMode.wipeEntireDrive) {
      // Mode 2 — no file explorer; same as CLI after drive pick.
      Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => DestructiveWarningScreen(
            api: widget.api,
            mode: widget.mode,
            targetPath: drivePath,
            targetIsFile: false,
          ),
        ),
      );
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => FileExplorerScreen(
          api: widget.api,
          mode: widget.mode,
          rootPath: drivePath,
        ),
      ),
    );
  }
}
