import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SubjectAnalyticsPage extends StatefulWidget {
  @override
  _SubjectAnalyticsPageState createState() => _SubjectAnalyticsPageState();
}

class _SubjectAnalyticsPageState extends State<SubjectAnalyticsPage> {
  List<dynamic> semesters = [];
  List<dynamic> subjects = [];
  int? selectedSemesterId;
  bool isLoading = false;
  int currentPage = 1;
  bool hasMore = true;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    fetchAnalyticsData(page: currentPage);
  }

  Future<void> fetchAnalyticsData({int page = 1}) async {
    if (isLoading) return;

    setState(() {
      isLoading = true;
    });

    try {
      final queryParameters = {
        if (selectedSemesterId != null) 'semester_id': selectedSemesterId.toString(),
        'page': page.toString(),
      };

      final uri = Uri.http('127.0.0.1:5000', '/subjects/analytics', queryParameters);
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        setState(() {
          currentPage = page;
          semesters = data['semesters'];
          subjects = data['subjects'];
          hasMore = subjects.isNotEmpty;
        });
      } else {
        throw Exception('Failed to load analytics');
      }
    } catch (e) {
      print('Error: $e');
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void onSemesterChanged(int? semesterId) {
    setState(() {
      selectedSemesterId = semesterId;
      currentPage = 1;
      subjects.clear();
    });
    fetchAnalyticsData(page: 1);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Subject Analytics'),
      ),
      body: isLoading && subjects.isEmpty
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: DropdownButtonFormField<int>(
                    value: selectedSemesterId,
                    decoration: InputDecoration(
                      labelText: 'Select Semester',
                      border: OutlineInputBorder(),
                    ),
                    items: semesters.map<DropdownMenuItem<int>>((semester) {
                      return DropdownMenuItem<int>(
                        value: semester['id'],
                        child: Text(semester['label']),
                      );
                    }).toList(),
                    onChanged: (value) {
                      onSemesterChanged(value);
                    },
                  ),
                ),
                Expanded(
                  child: Column(
                    children: [
                      Expanded(
                        child: ListView.builder(
                          controller: _scrollController,
                          itemCount: subjects.length,
                          itemBuilder: (context, index) {
                            final subject = subjects[index];
                            return Card(
                              margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              child: ListTile(
                                title: Text('${subject['subject_code']} - ${subject['subject_description']}'),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    SizedBox(height: 8),
                                    Text('Average Grade: ${subject['average_grade']}%'),
                                    Text('Passing Rate: ${subject['passing_rate']}%'),
                                    Text('At Risk Rate: ${subject['at_risk_rate']}%'),
                                    Text('Top Grade: ${subject['top_grade']}'),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            ElevatedButton(
                              onPressed: currentPage > 1 && !isLoading
                                  ? () => fetchAnalyticsData(page: currentPage - 1)
                                  : null,
                              child: Text('Previous'),
                            ),
                            Text('Page $currentPage', style: TextStyle(fontSize: 12)),
                            ElevatedButton(
                              onPressed: hasMore && !isLoading
                                  ? () => fetchAnalyticsData(page: currentPage + 1)
                                  : null,
                              child: Text('Next'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
