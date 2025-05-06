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
                  child: ListView.builder(
                    itemCount: students.length,
                    itemBuilder: (context, index) {
                      final student = students[index];
                      final subjects = student['SubjectCodes'] ?? [];
                      final grades = student['Grades'] ?? [];

                      return Card(
                        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                student['student']['Name'] ?? 'Unknown',
                                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              SizedBox(height: 4),
                              Text('Course: ${student['student']['Course'] ?? 'N/A'}'),
                              Text('Semester: ${student['semester']['SchoolYear']} - ${student['semester']['Semester']}'),
                              Divider(height: 16),
                              ...List.generate(subjects.length, (subIndex) {
                                return Text(
                                  '${subjects[subIndex]} - Grade: ${grades[subIndex]}',
                                  style: TextStyle(
                                    color: (grades[subIndex] < 80) ? Colors.red : Colors.black,
                                  ),
                                );
                              }),
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
