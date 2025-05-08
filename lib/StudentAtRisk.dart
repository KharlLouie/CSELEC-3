import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class StudentRiskAnalyticsPage extends StatefulWidget {
  @override
  _StudentRiskAnalyticsPageState createState() =>
      _StudentRiskAnalyticsPageState();
}

class _StudentRiskAnalyticsPageState extends State<StudentRiskAnalyticsPage> {
  List<dynamic> semesters = [];
  List<dynamic> students = [];
  int? selectedSemesterId;
  bool isLoading = false;
  int currentPage = 1;
  bool hasMoreData = true;

  @override
  void initState() {
    super.initState();
    fetchAnalyticsData();
  }

  Future<void> fetchAnalyticsData() async {
    if (isLoading) return;

    setState(() => isLoading = true);

    try {
      final queryParameters = {
        'page': currentPage.toString(),
        'per_page': '10',
        if (selectedSemesterId != null) 'semester_id': selectedSemesterId.toString(),
      };

      final uri = Uri.http('127.0.0.1:5000', '/students/at_risk', queryParameters);
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          semesters = data['semesters'];
          students = data['data'];
          hasMoreData = data['data'].isNotEmpty; // Check if there are more pages
        });
      } else {
        throw Exception('Failed to load analytics');
      }
    } catch (e) {
      print('Error: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  void onSemesterChanged(int? semesterId) {
    setState(() {
      selectedSemesterId = semesterId;
      students.clear(); // Clear the student list when changing semester
      currentPage = 1; // Reset the page to 1 when changing semester
      hasMoreData = true; // Enable pagination for the new semester
    });
    fetchAnalyticsData();
  }

  void nextPage() {
    if (hasMoreData) {
      setState(() {
        currentPage++;
      });
      fetchAnalyticsData();
    }
  }

  void previousPage() {
    if (currentPage > 1) {
      setState(() {
        currentPage--;
      });
      fetchAnalyticsData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Students At Risk (Line of 7 Grades)'),
      ),
      body: isLoading && students.isEmpty
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      DropdownButtonFormField<int>(
                        value: selectedSemesterId,
                        decoration: InputDecoration(
                          labelText: 'Select Semester',
                          border: OutlineInputBorder(),
                        ),
                        items: semesters.map<DropdownMenuItem<int>>((semester) {
                          return DropdownMenuItem<int>(
                            value: semester['semester_id'],
                            child: Text('${semester['school_year']} - ${semester['semester_name']}'),
                          );
                        }).toList(),
                        onChanged: onSemesterChanged,
                      ),
                      SizedBox(height: 8),
                    ],
                  ),
                ),
                Expanded(
                  child: Container(
                    width: 1900,
                    //scrollDirection: Axis.vertical,
                    child: DataTable(
                      decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  boxShadow: [
                                    BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                  ],
                                ),
                      columns: const [
                        DataColumn(label: Text('Student ID')),
                        DataColumn(label: Text('Course')),
                        DataColumn(label: Text('Year and Semester')),
                        DataColumn(label: Text('Risk Factors')),
                      ],
                      rows: students.map<DataRow>((student) {
                        final subjects = student['SubjectCodes'] ?? [];
                        final grades = student['Grades'] ?? [];
                        final riskFactors = <String>[];
                        for (int i = 0; i < subjects.length; i++) {
                          final grade = grades[i];
                          if (grade >= 70 && grade <= 79) {
                            riskFactors.add('${subjects[i]}: $grade');
                          }
                        }
                        return DataRow(cells: [
                          DataCell(Text(student['student']['_id']?.toString() ?? 'Unknown')),
                          DataCell(Text(student['student']['Course'] ?? 'N/A')),
                          DataCell(Text('${student['semester']['SchoolYear']} - ${student['semester']['Semester']}')),
                          DataCell(
                            riskFactors.isNotEmpty
                              ? SizedBox(
                                  height: 80, // Set your preferred max height here
                                  child: SingleChildScrollView(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      mainAxisSize: MainAxisSize.min,
                                      children: riskFactors
                                          .map((rf) => Text(rf, style: TextStyle(color: Colors.red)))
                                          .toList(),
                                    ),
                                  ),
                                )
                              : const Text('None'),
                          ),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton(
                        onPressed: previousPage,
                        child: Text('Previous Page'),
                      ),
                      Text('Page $currentPage', style: TextStyle(fontSize: 12)),
                      ElevatedButton(
                        onPressed: nextPage,
                        child: Text('Next Page'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
