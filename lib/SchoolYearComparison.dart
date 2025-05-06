import 'package:flutter/material.dart';

class SchoolYearComparisonReport extends StatelessWidget {
  const SchoolYearComparisonReport({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('School Year Comparison Report')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.count(
          crossAxisCount: 2,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          children: List.generate(4, (index) {
            return Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                color: Colors.orange[100],
              ),
            );
          }),
        ),
      ),
    );
  }
}
