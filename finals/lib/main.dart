import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:finals/StudentAtRisk.dart';
import 'package:finals/SubjectAnalytics.dart';
import 'package:finals/SubjectPerformance.dart';
import 'package:finals/ModifyData.dart';
import 'package:window_manager/window_manager.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'host_info.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  
  // Initialize window manager only on desktop platforms
  if (!kIsWeb) {
    await windowManager.ensureInitialized();
    await windowManager.maximize();
  }
  
  runApp(StudentDashboardApp());
}

class StudentDashboardApp extends StatelessWidget {
  const StudentDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: StudentDashboard(),
    );
  }
}

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  _StudentDashboardState createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard> with SingleTickerProviderStateMixin {
  final Color primaryColor = Color(0xFF5A67D8);
  final Color backgroundColor = Color(0xFFF7FAFC);
  final TextEditingController _urlController = TextEditingController();

  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _contentSlideAnimation;

  bool isSidebarOpen = false; // Track sidebar state

  int? selectedSchoolYear;
  String? selectedSemester;

  List<int> schoolYears = [];

  double? passingRate;
  double? atRiskRate;
  double? averageGrade;
  double? topGrade;

  // Add state variables for both semesters
  double? firstSemAverageGrade;
  double? firstSemPassingRate;
  double? firstSemAtRiskRate;
  double? firstSemTopGrade;

  double? secondSemAverageGrade;
  double? secondSemPassingRate;
  double? secondSemAtRiskRate;
  double? secondSemTopGrade;

  // Add state variables for Summer semester
  double? summerAverageGrade;
  double? summerPassingRate;
  double? summerAtRiskRate;
  double? summerTopGrade;

  @override
  void initState() {
    super.initState();
    _urlController.text = apiBaseUrl;  // Initialize with current URL

    _controller = AnimationController(
      duration: Duration(milliseconds: 600),
      vsync: this,
    );

    _slideAnimation = Tween<Offset>(begin: Offset(-1.0, 0.0), end: Offset.zero).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    ));

    _contentSlideAnimation = Tween<Offset>(begin: Offset(1.1, 0.0), end: Offset.zero).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    ));

    fetchSchoolYears();
  }

  Future<void> fetchSchoolYears() async {
    final url = Uri.parse(
      apiBaseUrl.startsWith('http') ? '$apiBaseUrl/home/' : 'http://$apiBaseUrl/home/'
    );
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          schoolYears = List<int>.from(data['school_years']);
        });
      }
    } catch (e) {
      print("Error fetching school years: $e");
    }
  }

  Future<void> fetchSemesterData() async {
    if (selectedSchoolYear == null) return;

    final url = Uri.parse(
      apiBaseUrl.startsWith('http') ? '$apiBaseUrl/home/?sy=$selectedSchoolYear' : 'http://$apiBaseUrl/home/?sy=$selectedSchoolYear'
    );
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List semestersData = data['semesters'];

        final firstSemData = semestersData.firstWhere(
          (s) => s['semester_name'] == 'FirstSem',
          orElse: () => null,
        );
        final secondSemData = semestersData.firstWhere(
          (s) => s['semester_name'] == 'SecondSem',
          orElse: () => null,
        );
        final summerSemData = semestersData.firstWhere(
          (s) => s['semester_name'] == 'Summer',
          orElse: () => null,
        );

        setState(() {
          firstSemAverageGrade = firstSemData != null ? firstSemData['average_grade']?.toDouble() : null;
          firstSemPassingRate = firstSemData != null ? firstSemData['passing_rate']?.toDouble() : null;
          firstSemAtRiskRate = firstSemData != null ? firstSemData['at_risk_rate']?.toDouble() : null;
          firstSemTopGrade = firstSemData != null ? firstSemData['top_grade']?.toDouble() : null;

          secondSemAverageGrade = secondSemData != null ? secondSemData['average_grade']?.toDouble() : null;
          secondSemPassingRate = secondSemData != null ? secondSemData['passing_rate']?.toDouble() : null;
          secondSemAtRiskRate = secondSemData != null ? secondSemData['at_risk_rate']?.toDouble() : null;
          secondSemTopGrade = secondSemData != null ? secondSemData['top_grade']?.toDouble() : null;

          summerAverageGrade = summerSemData != null ? summerSemData['average_grade']?.toDouble() : null;
          summerPassingRate = summerSemData != null ? summerSemData['passing_rate']?.toDouble() : null;
          summerAtRiskRate = summerSemData != null ? summerSemData['at_risk_rate']?.toDouble() : null;
          summerTopGrade = summerSemData != null ? summerSemData['top_grade']?.toDouble() : null;
        });
      }
    } catch (e) {
      print("Error fetching semester data: $e");
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _urlController.dispose();  // Dispose the controller
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    List<int> displayedSchoolYears = schoolYears.isNotEmpty
        ? schoolYears
        : [2020, 2021, 2022, 2023, 2024]; // Fallback if Flask offline

    return Scaffold(
      backgroundColor: backgroundColor,
      body: Stack(
        children: [
          // Slide all content together
          SlideTransition(
            position: _slideAnimation,
            child: Row(
              children: [
                // Sidebar
                Container(
                  width: 250,
                  color: primaryColor,
                  padding: EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(height: 90),
                      Text(
                        'Commands',
                        style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 20),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (context) => StudentPerformancePage()));
                        },
                        child: Text('Fetch Student Performance', style: TextStyle(color: Colors.white)),
                      ),
                      SizedBox(height: 10),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (context) => StudentRiskAnalyticsPage()));
                        },
                        child: Text('Fetch At-Risk Students', style: TextStyle(color: Colors.white)),
                      ),
                      SizedBox(height: 10),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (context) => SubjectAnalyticsPage()));
                        },
                        child: Text('Fetch Subject Analytics', style: TextStyle(color: Colors.white)),
                      ),
                      SizedBox(height: 10),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (context) => ModifyDataPage()));
                        },
                        child: Text('Modify Data', style: TextStyle(color: Colors.white)),
                      ),
                    ],
                  ),
                ),

                // Slide content separately for subtle animation effect
                Expanded(
                  child: SlideTransition(
                    position: _contentSlideAnimation,
                    child: Stack(
                      children: [
                        // Background content
                        Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Performance Dashboard',
                                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.black87)),
                              SizedBox(height: 20),

                              // School Year Dropdown
                              Text('School Year:',
                                  style: TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
                              SizedBox(height: 8),
                              Container(
                                width: double.infinity,
                                padding: EdgeInsets.symmetric(horizontal: 16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  boxShadow: [
                                    BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                  ],
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<int>(
                                    value: selectedSchoolYear,
                                    hint: Text("Select School Year"),
                                    onChanged: (value) {
                                      setState(() {
                                        selectedSchoolYear = value;
                                        selectedSemester = null;
                                      });
                                      fetchSemesterData();
                                    },
                                    items: displayedSchoolYears.map((year) {
                                      return DropdownMenuItem<int>(
                                        value: year,
                                        child: Text(year.toString()),
                                      );
                                    }).toList(),
                                  ),
                                ),
                              ),

                              SizedBox(height: 60),

                              // Table for metrics
                              SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: Container(
                                  width: null,
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(12),
                                    boxShadow: [
                                      BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                    ],
                                  ),
                                  child: DataTable(
                                    columns: const [
                                      DataColumn(label: Text('Metric', style: TextStyle(fontWeight: FontWeight.bold))),
                                      DataColumn(label: Text('First Semester', style: TextStyle(fontWeight: FontWeight.bold))),
                                      DataColumn(label: Text('Second Semester', style: TextStyle(fontWeight: FontWeight.bold))),
                                      DataColumn(label: Text('Summer Semester', style: TextStyle(fontWeight: FontWeight.bold))),
                                      DataColumn(label: Text('Change (1st and 2nd Semester)', style: TextStyle(fontWeight: FontWeight.bold))),
                                    ],
                                    rows: [
                                      DataRow(cells: [
                                        const DataCell(Text('Average GPA')),
                                        DataCell(Text(firstSemAverageGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text(secondSemAverageGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text(summerAverageGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text((secondSemAverageGrade != null && firstSemAverageGrade != null) ? (secondSemAverageGrade! - firstSemAverageGrade!).toStringAsFixed(2) : 'N/A')),
                                      ]),
                                      DataRow(cells: [
                                        const DataCell(Text('Passing Rate (%)')),
                                        DataCell(_percentCell(firstSemPassingRate)),
                                        DataCell(_percentCell(secondSemPassingRate)),
                                        DataCell(_percentCell(summerPassingRate)),
                                        DataCell(_percentCell((secondSemPassingRate != null && firstSemPassingRate != null) ? (secondSemPassingRate! - firstSemPassingRate!) : null)),
                                      ]),
                                      DataRow(cells: [
                                        const DataCell(Text('Top Grade')),
                                        DataCell(Text(firstSemTopGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text(secondSemTopGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text(summerTopGrade?.toStringAsFixed(2) ?? 'N/A')),
                                        DataCell(Text((secondSemTopGrade != null && firstSemTopGrade != null) ? (secondSemTopGrade! - firstSemTopGrade!).toStringAsFixed(2) : 'N/A')),
                                      ]),
                                      DataRow(cells: [
                                        const DataCell(Text('At-Risk Students (%)')),
                                        DataCell(_percentCell(firstSemAtRiskRate)),
                                        DataCell(_percentCell(secondSemAtRiskRate)),
                                        DataCell(_percentCell(summerAtRiskRate)),
                                        DataCell(_percentCell((secondSemAtRiskRate != null && firstSemAtRiskRate != null) ? (secondSemAtRiskRate! - firstSemAtRiskRate!) : null)),
                                      ]),
                                    ],
                                  ),
                                ),
                              ),
                              SizedBox(height: 30),
                              
                              /*
                              // URL Input Field
                              Container(
                                width: double.infinity,
                                padding: EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  boxShadow: [
                                    BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                  ],
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Host Address (Developer Test)',
                                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                    SizedBox(height: 8),
                                    Row(
                                      children: [
                                        Expanded(
                                          child: TextField(
                                            controller: _urlController,
                                            decoration: InputDecoration(
                                              hintText: 'Enter Host Address and Port (ex. 127.0.0.1:5000)',
                                              border: OutlineInputBorder(
                                                borderRadius: BorderRadius.circular(8),
                                              ),
                                              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                            ),
                                          ),
                                        ),
                                        SizedBox(width: 8),
                                        ElevatedButton(
                                          onPressed: () {
                                            setState(() {
                                              apiBaseUrl = _urlController.text;
                                            });
                                            ScaffoldMessenger.of(context).showSnackBar(
                                              SnackBar(
                                                content: Text('Address updated successfully'),
                                                duration: Duration(seconds: 2),
                                              ),
                                            );
                                          },
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: primaryColor,
                                            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                          ),
                                          child: Text('Update Address' , style: TextStyle(color: Colors.white)),
                                        ),
                                      ],
                                    ),
                                  ],
                                ), 
                              ),*/
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Burger button always visible
          Positioned(
            top: 40,
            left: 20,
            child: IconButton(
              icon: Icon(Icons.menu, color: Colors.black, size: 40),
              onPressed: () {
                setState(() {
                  if (isSidebarOpen) {
                    _controller.reverse(); // Close sidebar
                  } else {
                    _controller.forward(); // Open sidebar
                  }
                  isSidebarOpen = !isSidebarOpen; // Toggle the sidebar state
                });
              },
            ),
          ),
        ],
      ),
    );
  }

  // Helper widget for percentage display
  Widget _percentCell(double? value) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(value != null ? value.toStringAsFixed(2) : 'N/A'),
        SizedBox(width: 4),
        Text('%', style: TextStyle(color: Colors.grey)),
      ],
    );
  }
}