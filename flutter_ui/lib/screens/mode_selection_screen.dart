import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import 'drive_selection_screen.dart';

/// Step 1 — mirrors ``main.py`` mode menu.
class ModeSelectionScreen extends StatelessWidget {
  const ModeSelectionScreen({super.key, required this.api});

  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ZeroTrace Secure Data Sanitization Tool'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                'Select Mode:',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              _modeTile(
                context,
                title: '1. Wipe User Data (Navigate & Delete)',
                subtitle: 'Choose drive, browse folders/files, then wipe.',
                mode: AppMode.wipeUserData,
              ),
              _modeTile(
                context,
                title: '2. Wipe Entire Drive',
                subtitle: 'Pick a drive/root, then confirm and wipe (no explorer).',
                mode: AppMode.wipeEntireDrive,
              ),
              _modeTile(
                context,
                title: '3. Overwrite Only (Keep File, Wipe Content)',
                subtitle: 'Browse to a file, overwrite in place (no delete).',
                mode: AppMode.overwriteOnly,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _modeTile(
    BuildContext context, {
    required String title,
    required String subtitle,
    required AppMode mode,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => DriveSelectionScreen(api: api, mode: mode),
            ),
          );
        },
      ),
    );
  }
}
