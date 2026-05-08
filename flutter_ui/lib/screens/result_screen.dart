import 'package:flutter/material.dart';
import 'package:open_file/open_file.dart';

import '../services/api_client.dart';

/// Step 7 — summary, certificate paths, and structure-removal demonstration.
class ResultScreen extends StatefulWidget {
  const ResultScreen({
    super.key,
    required this.api,
    required this.jobStatus,
    required this.success,
    required this.originalTargetPath,
    this.errorText,
  });

  final ApiClient api;
  final JobStatus? jobStatus;
  final bool success;
  final String originalTargetPath;
  final String? errorText;

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  late final Future<bool> _livePathExists;

  @override
  void initState() {
    super.initState();
    _livePathExists = widget.api.pathExists(widget.originalTargetPath);
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.jobStatus?.result;
    final cert = r != null ? r['certificate'] as Map<String, dynamic>? : null;
    final certErr = r != null ? r['certificate_error'] as String? : null;
    final passed = r != null ? r['passed'] : null;
    final failed = r != null ? r['failed'] : null;
    final total = r != null ? r['total'] : null;
    final demo = r != null ? r['demonstration'] as Map<String, dynamic>? : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Result'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Icon(
            widget.success ? Icons.check_circle : Icons.error_outline,
            size: 72,
            color: widget.success ? Colors.green : Colors.red,
          ),
          const SizedBox(height: 12),
          Text(
            widget.success
                ? 'Operation finished successfully'
                : 'Operation failed or incomplete',
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
          ),
          if (widget.errorText != null) ...[
            const SizedBox(height: 12),
            SelectableText(widget.errorText!),
          ],
          if (widget.jobStatus?.error != null) ...[
            const SizedBox(height: 12),
            SelectableText(widget.jobStatus!.error!),
          ],
          const Divider(height: 32),
          Text(
            'File structure & path verification',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          _buildDemonstration(context, demo),
          const SizedBox(height: 8),
          FutureBuilder<bool>(
            future: _livePathExists,
            builder: (context, snap) {
              if (snap.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: LinearProgressIndicator(),
                );
              }
              if (snap.hasError) {
                return Text('Live path check failed: ${snap.error}');
              }
              final live = snap.data ?? false;
              return Text(
                'Live GET /api/path-exists: "${widget.originalTargetPath}" → exists=$live',
                style: Theme.of(context).textTheme.bodySmall,
              );
            },
          ),
          const Divider(height: 32),
          Text('========== SUMMARY ==========', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Text('Total   : ${total ?? "-"}'),
          Text('Passed  : ${passed ?? "-"}'),
          Text('Failed  : ${failed ?? "-"}'),
          if (certErr != null) ...[
            const SizedBox(height: 12),
            Text('Certificate error: $certErr'),
          ],
          if (cert != null) ...[
            const SizedBox(height: 16),
            Text('Tamper-proof certificate:', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            SelectableText(cert['certificate_json']?.toString() ?? ''),
            const SizedBox(height: 8),
            SelectableText(cert['signature_sig']?.toString() ?? ''),
            const SizedBox(height: 8),
            SelectableText(cert['certificate_pdf']?.toString() ?? ''),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () async {
                final pdf = cert['certificate_pdf']?.toString();
                if (pdf == null || pdf.isEmpty) return;
                await OpenFile.open(pdf);
              },
              icon: const Icon(Icons.picture_as_pdf),
              label: const Text('Open certificate (PDF)'),
            ),
          ],
          const SizedBox(height: 24),
          FilledButton(
            onPressed: () {
              Navigator.of(context).popUntil((route) => route.isFirst);
            },
            child: const Text('Back to home'),
          ),
        ],
      ),
    );
  }

  Widget _buildDemonstration(BuildContext context, Map<String, dynamic>? demo) {
    if (demo == null) {
      return Text(
        'No demonstration payload from server.',
        style: Theme.of(context).textTheme.bodySmall,
      );
    }

    final overwrite = demo['overwrite_only'] == true;
    final wasFile = demo['target_was_file'] == true;
    final existsAfter = demo['path_exists_after_wipe'] == true;
    final ok = widget.success;

    if (overwrite) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _demoRow(
            context,
            true,
            'File still exists at path (overwrite-only — expected)',
          ),
          _demoRow(context, ok, 'User data overwritten in place'),
          _demoRow(context, ok, 'Original filename retained'),
        ],
      );
    }

    if (wasFile) {
      final gone = !existsAfter;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _demoRow(
            context,
            gone,
            'File no longer exists in filesystem (original path)',
          ),
          _demoRow(context, ok, 'Space reclaimed (file unlinked)'),
          _demoRow(context, ok, 'Data overwritten (NIST passes completed)'),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _demoRow(
          context,
          ok,
          'Contained files processed; folder path may still exist (directory entry)',
        ),
        _demoRow(context, ok, 'Space reclaimed for removed files'),
        _demoRow(context, ok, 'Data overwritten (NIST passes completed)'),
      ],
    );
  }

  Widget _demoRow(BuildContext context, bool ok, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            ok ? Icons.check_circle : Icons.cancel,
            color: ok ? Colors.green : Colors.orange,
            size: 22,
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(label)),
        ],
      ),
    );
  }
}
