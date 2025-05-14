import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'host_info.dart';

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

      final uri = Uri.http(apiBaseUrl, '/subjects/analytics', queryParameters);
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
                      prefixIcon: Icon(Icons.calendar_month_rounded),
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
                        child: Container(
                          width: double.infinity,
                          //scrollDirection: Axis.horizontal,
                          child: SingleChildScrollView(
                            child: DataTable(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                boxShadow: [
                                  BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                ],
                              ),
                              columns: const [
                                DataColumn(label: Text('Subject Code')),
                                DataColumn(label: Text('Description')),
                                DataColumn(label: Text('Average Grade')),
                                DataColumn(label: Text('Passing Rate Percentage')),
                                DataColumn(label: Text('At-Risk Rate Percentage')),
                                DataColumn(label: Text('Top Grade')),
                              ],
                              rows: subjects.map<DataRow>((subject) {
                                return DataRow(
                                  cells: [
                                    DataCell(Text(subject['subject_code'].toString())),
                                    DataCell(Text(subject['subject_description'].toString())),
                                    DataCell(Text('${subject['average_grade']}%')),
                                    DataCell(Text('${subject['passing_rate']}%')),
                                    DataCell(Text('${subject['at_risk_rate']}%')),
                                    DataCell(Text(subject['top_grade'].toString())),
                                  ],
                                );
                              }).toList(),
                            ),
                          ),
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
