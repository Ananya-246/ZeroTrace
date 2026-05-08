import 'package:flutter/material.dart';

/// CLI parity: user must type exactly ``YES`` (case-sensitive, like ``main.py``).
Future<bool> showYesConfirmDialog(
  BuildContext context, {
  required String title,
  required String body,
  String confirmLabel = 'Continue',
}) async {
  final controller = TextEditingController();
  final ok = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (ctx) {
      return AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(body),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                decoration: const InputDecoration(
                  labelText: 'Type YES to continue',
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (controller.text.trim() == 'YES') {
                Navigator.of(ctx).pop(true);
              } else {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('You must type exactly YES')),
                );
              }
            },
            child: Text(confirmLabel),
          ),
        ],
      );
    },
  );
  controller.dispose();
  return ok ?? false;
}
