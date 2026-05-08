import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import '../widgets/yes_confirm_dialog.dart';
import 'progress_screen.dart';

/// Step 5 — mirrors ``main.py`` NIST Clear / Purge choice.
///
/// Destructive flow also shows ``Found N file(s)`` after the first YES, like CLI.
class WipeMethodScreen extends StatefulWidget {
  const WipeMethodScreen({
    super.key,
    required this.api,
    required this.mode,
    required this.targetPath,
    required this.targetIsFile,
    required this.isOverwrite,
  });

  final ApiClient api;
  final AppMode mode;
  final String targetPath;
  final bool targetIsFile;

  /// When true, titles match Mode 3 (overwrite) instead of secure delete.
  final bool isOverwrite;

  @override
  State<WipeMethodScreen> createState() => _WipeMethodScreenState();
}

class _WipeMethodScreenState extends State<WipeMethodScreen> {
  late Future<int> _countFuture;
  String _nistChoice = 'clear'; // 'clear' | 'purge'

  @override
  void initState() {
    super.initState();
    if (widget.isOverwrite) {
      _countFuture = Future.value(1);
    } else {
      _countFuture = widget.api.fileCount(widget.targetPath);
    }
  }

  Future<void> _proceed(BuildContext context) async {
    final ok = await showYesConfirmDialog(
      context,
      title: 'Final confirmation',
      body: 'Proceed? Type YES to confirm.',
      confirmLabel: 'Start',
    );
    if (!ok || !context.mounted) return;

    await Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(
        builder: (_) => ProgressScreen(
          api: widget.api,
          mode: widget.mode,
          targetPath: widget.targetPath,
          targetIsFile: widget.targetIsFile,
          nistMethod: _nistChoice,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.isOverwrite ? 'Overwrite Method' : 'Wipe Method'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: FutureBuilder<int>(
            future: _countFuture,
            builder: (context, snap) {
              if (snap.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snap.hasError) {
                return Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Error: ${snap.error}'),
                );
              }
              final n = snap.data ?? 0;
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  if (!widget.isOverwrite) ...[
                    Text(
                      'Found $n file(s)',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 16),
                  ],
                  Text(
                    widget.isOverwrite
                        ? 'Select Overwrite Method:'
                        : 'Select Wipe Method:',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 8),
                  RadioListTile<String>(
                    title: const Text('NIST Clear (1-pass)'),
                    value: 'clear',
                    groupValue: _nistChoice,
                    onChanged: (v) => setState(() => _nistChoice = v!),
                  ),
                  RadioListTile<String>(
                    title: const Text('NIST Purge (3-pass)'),
                    value: 'purge',
                    groupValue: _nistChoice,
                    onChanged: (v) => setState(() => _nistChoice = v!),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: () => _proceed(context),
                    child: const Text('Proceed…'),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
