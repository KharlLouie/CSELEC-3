import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_screenutil/flutter_screenutil.dart';

import 'host_info.dart';
import 'package:finals/StudentAtRisk.dart';
import 'package:finals/SubjectAnalytics.dart';
import 'package:finals/SubjectPerformance.dart';
import 'package:finals/ModifyData.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);

  runApp(const AppWrapper());
}

class AppWrapper extends StatelessWidget {
  const AppWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    // Use a MaterialApp to provide MediaQuery context
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Builder(
        builder: (context) {
          return ScreenUtilInit(
            designSize: Size(690,360),
            minTextAdapt: true,
            splitScreenMode: true,
            builder: (_, child) => child!,
            child: const StudentDashboard(),
          );
        },
      ),
    );
  }
}

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  State<StudentDashboard> createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard>
    with AutomaticKeepAliveClientMixin {
  final Color primaryColor = const Color(0xFF5A67D8);
  final Color backgroundColor = const Color(0xFFF7FAFC);
  final TextEditingController _urlController = TextEditingController();
  final ScrollController scrollController = ScrollController();

  int? selectedSchoolYear;
  int highlightedIndex = 0;
  List<int> schoolYears = [];

  final Map<String, Map<String, double?>> semesterData = {
    'FirstSem': {},
    'SecondSem': {},
    'Summer': {},
  };

  @override
  bool get wantKeepAlive => false;

  @override
  void initState() {
    super.initState();
    _urlController.text = apiBaseUrl;
    fetchSchoolYears();
  }

  @override
  void dispose() {
    _urlController.dispose();
    scrollController.dispose();
    super.dispose();
  }

  Future<void> fetchSchoolYears() async {
    final url = Uri.parse('http://$apiBaseUrl/home/');
    try {
      final response = await http.get(url, headers: {'Cache-Control': 'no-cache'});
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final years = List<int>.from(data['school_years']);
        setState(() {
          schoolYears = years;
          if (years.isNotEmpty) {
            selectedSchoolYear = years.first;
            highlightedIndex = 0;
            fetchSemesterData();
          }
        });
      }
    } catch (e) {
      debugPrint("Error fetching school years: $e");
    }
  }

  Future<void> fetchSemesterData() async {
    if (selectedSchoolYear == null) return;
    final url = Uri.parse(
        'http://$apiBaseUrl/home/?sy=$selectedSchoolYear&timestamp=${DateTime.now().millisecondsSinceEpoch}');
    try {
      final response = await http.get(url, headers: {'Cache-Control': 'no-cache'});
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List semesters = data['semesters'];

        for (final name in semesterData.keys) {
          final semester = semesters.firstWhere(
            (s) => s['semester_name'] == name,
            orElse: () => null,
          );
          semesterData[name] = {
            'average_grade': semester?['average_grade']?.toDouble(),
            'passing_rate': semester?['passing_rate']?.toDouble(),
            'at_risk_rate': semester?['at_risk_rate']?.toDouble(),
            'top_grade': semester?['top_grade']?.toDouble(),
          };
        }

        setState(() {});
      }
    } catch (e) {
      debugPrint("Error fetching semester data: $e");
    }
  }

  Widget _percentCell(double? value) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(value?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp)),
        SizedBox(width: 4.w),
        Text('%', style: TextStyle(color: Colors.grey, fontSize: 6.sp)),
      ],
    );
  }

  Widget _buildSidebarItem(String label, Widget page) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 5.h),
      child: GestureDetector(
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => page)),
        child: Text(label, style: TextStyle(color: Colors.white, fontSize: 6.sp)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context); // for AutomaticKeepAliveClientMixin

    final first = semesterData['FirstSem']!;
    final second = semesterData['SecondSem']!;
    final summer = semesterData['Summer']!;
    final displayedYears = schoolYears.isNotEmpty ? schoolYears : [2020, 2021, 2022, 2023, 2024];

    return Scaffold(
      backgroundColor: backgroundColor,
      body: Row(
        children: [
          Container(
            width: 250.w,
            color: primaryColor,
            padding: EdgeInsets.all(20.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 10.h),
                Text('Commands', style: TextStyle(color: Colors.white, fontSize: 15.sp, fontWeight: FontWeight.bold)),
                SizedBox(height: 10.h),
                _buildSidebarItem('Fetch Student Performance', StudentPerformancePage()),
                _buildSidebarItem('Fetch At-Risk Students', StudentRiskAnalyticsPage()),
                _buildSidebarItem('Fetch Subject Analytics', SubjectAnalyticsPage()),
                _buildSidebarItem('Modify Data', const ModifyDataPage()),
              ],
            ),
          ),
Expanded(
  child: Padding(
    padding: EdgeInsets.all(24.w),
    child: SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Performance Dashboard',
            style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.bold, color: Colors.black87),
          ),
          SizedBox(height: 5.h),
          DropdownButtonFormField<int>(
            value: selectedSchoolYear,
            decoration: InputDecoration(
              labelText: 'Select School Year',
              labelStyle: TextStyle(fontSize: 7.sp),
              border: const OutlineInputBorder(),
              contentPadding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
            ),
            isExpanded: true,
            items: displayedYears
                .map((year) => DropdownMenuItem(
                      value: year,
                      child: Text('$year', style: TextStyle(fontSize: 7.sp)),
                    ))
                .toList(),
            onChanged: (newValue) {
              if (newValue != null) {
                setState(() {
                  selectedSchoolYear = newValue;
                  highlightedIndex = displayedYears.indexOf(newValue);
                });
                fetchSemesterData();
              }
            },
            dropdownColor: Colors.white,
            icon: const Icon(Icons.arrow_drop_down),
            menuMaxHeight: 160.h,
          ),
          SizedBox(height: 10.h),
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12.r),
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 6.r, offset: Offset(0, 2))],
            ),
            child: DataTable(
              columnSpacing: 10.w,
              columns: [
                DataColumn(label: Text('Metric', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 6.sp))),
                DataColumn(label: Text('First Semester', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 6.sp))),
                DataColumn(label: Text('Second Semester', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 6.sp))),
                DataColumn(label: Text('Summer Semester', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 6.sp))),
                DataColumn(label: Text('Change (1st to 2nd Sem)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 6.sp))),
              ],
              rows: [
                DataRow(cells: [
                  DataCell(Text('Average GPA', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(first['average_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(second['average_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(summer['average_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(
                      (first['average_grade'] != null && second['average_grade'] != null)
                          ? (second['average_grade']! - first['average_grade']!).toStringAsFixed(2)
                          : 'N/A',
                      style: TextStyle(fontSize: 6.sp))),
                ]),
                DataRow(cells: [
                  DataCell(Text('Passing Rate (%)', style: TextStyle(fontSize: 6.sp))),
                  DataCell(_percentCell(first['passing_rate'])),
                  DataCell(_percentCell(second['passing_rate'])),
                  DataCell(_percentCell(summer['passing_rate'])),
                  DataCell(_percentCell(
                      (first['passing_rate'] != null && second['passing_rate'] != null)
                          ? (second['passing_rate']! - first['passing_rate']!)
                          : null)),
                ]),
                DataRow(cells: [
                  DataCell(Text('Top Grade', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(first['top_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(second['top_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(summer['top_grade']?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 6.sp))),
                  DataCell(Text(
                      (first['top_grade'] != null && second['top_grade'] != null)
                          ? (second['top_grade']! - first['top_grade']!).toStringAsFixed(2)
                          : 'N/A',
                      style: TextStyle(fontSize: 6.sp))),
                ]),
                DataRow(cells: [
                  DataCell(Text('At-Risk Students (%)', style: TextStyle(fontSize: 6.sp))),
                  DataCell(_percentCell(first['at_risk_rate'])),
                  DataCell(_percentCell(second['at_risk_rate'])),
                  DataCell(_percentCell(summer['at_risk_rate'])),
                  DataCell(_percentCell(
                      (first['at_risk_rate'] != null && second['at_risk_rate'] != null)
                          ? (second['at_risk_rate']! - first['at_risk_rate']!)
                          : null)),
                ]),
              ],
            ),
          ),
          SizedBox(height: 20.h), // bottom spacing so content doesn't get cut off
        ],
      ),
    ),
  ),
),

        ],
      ),
    );
  }
}
