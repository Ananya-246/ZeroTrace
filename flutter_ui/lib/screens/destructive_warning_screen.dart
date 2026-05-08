import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import '../widgets/yes_confirm_dialog.dart';
import 'wipe_method_screen.dart';

/// Step 4 — first ``main.py`` confirmation:
/// ``WARNING: This will permanently delete`` + ``Type YES``.
class DestructiveWarningScreen extends StatelessWidget {
  const DestructiveWarningScreen({
    super.key,
    required this.api,
    required this.mode,
    required this.targetPath,
    required this.targetIsFile,
  });

  final ApiClient api;
  final AppMode mode;
  final String targetPath;
  final bool targetIsFile;

  Future<void> _continue(BuildContext context) async {
    final ok = await showYesConfirmDialog(
      context,
      title: 'Confirm permanent deletion',
      body:
          '⚠ WARNING: This will permanently delete:\n\n$targetPath\n\n'
          'Type YES to continue.',
      confirmLabel: 'Continue',
    );
    if (!ok || !context.mounted) return;

    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => WipeMethodScreen(
          api: api,
          mode: mode,
          targetPath: targetPath,
          targetIsFile: targetIsFile,
          isOverwrite: false,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirmation'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  '⚠ WARNING: This will permanently delete:',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                SelectableText(targetPath),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: () => _continue(context),
                  child: const Text('Continue to confirmation (type YES)'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
