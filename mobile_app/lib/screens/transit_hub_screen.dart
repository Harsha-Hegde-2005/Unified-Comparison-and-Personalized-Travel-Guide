import 'package:flutter/material.dart';
import '../services/api_service.dart';

class TransitHubScreen extends StatelessWidget {
  const TransitHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    final List<Map<String, dynamic>> tools = [
      {
        'title': 'Bus Route Lookup',
        'desc': 'Look up bus stops along routes.',
        'icon': Icons.alt_route,
        'color': const Color(0xFF7C5CFF),
        'view': const BusRouteLookupView(),
      },
      {
        'title': 'Route Timetable',
        'desc': 'View schedules and departures.',
        'icon': Icons.schedule,
        'color': Colors.orange,
        'view': const RouteTimetableView(),
      },
      {
        'title': 'Stop Arrivals Info',
        'desc': 'Search upcoming stop arrivals.',
        'icon': Icons.directions_bus,
        'color': Colors.teal,
        'view': const StopArrivalsView(),
      },
      {
        'title': 'Weather Forecast',
        'desc': 'Check precipitation and temperature.',
        'icon': Icons.wb_sunny_outlined,
        'color': Colors.amber,
        'view': const WeatherReportView(),
      },
      {
        'title': 'Fare Calculator',
        'desc': 'Compare fares across all modes.',
        'icon': Icons.calculate_outlined,
        'color': const Color(0xFF10B981),
        'view': const FareCalculatorView(),
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transit Tools', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: cardBgColor,
        elevation: 1,
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: tools.length,
        itemBuilder: (context, index) {
          final tool = tools[index];
          return Card(
            color: cardBgColor,
            elevation: 2,
            margin: const EdgeInsets.symmetric(vertical: 8.0),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              leading: CircleAvatar(
                backgroundColor: tool['color'].withOpacity(0.15),
                child: Icon(tool['icon'], color: tool['color']),
              ),
              title: Text(tool['title'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              subtitle: Text(tool['desc'], style: const TextStyle(color: Colors.grey, fontSize: 13)),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => tool['view']),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 1. Bus Route Lookup View
// ─────────────────────────────────────────────────────────────
class BusRouteLookupView extends StatefulWidget {
  const BusRouteLookupView({super.key});

  @override
  State<BusRouteLookupView> createState() => _BusRouteLookupViewState();
}

class _BusRouteLookupViewState extends State<BusRouteLookupView> {
  final _controller = TextEditingController(text: '500D');
  Map<String, dynamic>? _data;
  bool _loading = false;

  void _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    setState(() => _loading = true);
    final res = await ApiService.fetchRouteDetails(query);
    setState(() {
      _data = res;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    return Scaffold(
      appBar: AppBar(title: const Text('Route Lookup')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      labelText: 'Route Number',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _search,
                  child: const Text('Search'),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_loading) const Center(child: CircularProgressIndicator()),
            if (!_loading && _data != null) ...[
              Card(
                color: cardBgColor,
                child: ListTile(
                  title: Text('Route ${_data!['route']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('Type: ${_data!['type']?.toString().toUpperCase()} • Stops: ${_data!['stop_count']}'),
                ),
              ),
              const SizedBox(height: 10),
              Expanded(
                child: ListView.builder(
                  itemCount: (_data!['stops'] as List<dynamic>?)?.length ?? 0,
                  itemBuilder: (context, idx) {
                    final stop = _data!['stops'][idx];
                    return ListTile(
                      leading: CircleAvatar(radius: 12, child: Text('${idx + 1}', style: const TextStyle(fontSize: 10))),
                      title: Text(stop.toString(), style: const TextStyle(fontSize: 14)),
                    );
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 2. Route Timetable View
// ─────────────────────────────────────────────────────────────
class RouteTimetableView extends StatefulWidget {
  const RouteTimetableView({super.key});

  @override
  State<RouteTimetableView> createState() => _RouteTimetableViewState();
}

class _RouteTimetableViewState extends State<RouteTimetableView> {
  final _routeController = TextEditingController(text: '500D');
  final _stopController = TextEditingController();
  Map<String, dynamic>? _data;
  bool _loading = false;
  String? _error;

  void _getTimetable() async {
    final route = _routeController.text.trim();
    if (route.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _data = null;
    });

    final stop = _stopController.text.trim().isEmpty ? null : _stopController.text.trim();
    final res = await ApiService.fetchRouteTimetable(route, stop);

    setState(() {
      _loading = false;
      if (res != null) {
        _data = res;
      } else {
        _error = 'Timetable not found for route $route';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Route Timetable')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _routeController,
              decoration: InputDecoration(
                labelText: 'Route Number (e.g. 500D)',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _stopController,
              decoration: InputDecoration(
                labelText: 'Stop Name (Optional)',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _getTimetable,
              child: const Text('Get Departures'),
            ),
            const SizedBox(height: 20),
            if (_loading) const Center(child: CircularProgressIndicator()),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            if (!_loading && _data != null) ...[
              ListTile(
                title: Text('Departures for Route ${_data!['route']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Stop: ${_data!['stop'] ?? 'Start Terminus'}'),
              ),
              const SizedBox(height: 10),
              Expanded(
                child: _data!['departures'] == null || (_data!['departures'] as List).isEmpty
                    ? const Center(child: Text('No departure timings registered.'))
                    : ListView.builder(
                        itemCount: (_data!['departures'] as List).length,
                        itemBuilder: (context, idx) {
                          final dep = _data!['departures'][idx];
                          return ListTile(
                            leading: const Icon(Icons.alarm, color: Colors.orange),
                            title: Text(dep.toString(), style: const TextStyle(fontWeight: FontWeight.bold)),
                          );
                        },
                      ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 3. Stop Arrivals Info View
// ─────────────────────────────────────────────────────────────
class StopArrivalsView extends StatefulWidget {
  const StopArrivalsView({super.key});

  @override
  State<StopArrivalsView> createState() => _StopArrivalsViewState();
}

class _StopArrivalsViewState extends State<StopArrivalsView> {
  final _controller = TextEditingController(text: 'Majestic');
  Map<String, dynamic>? _data;
  bool _loading = false;

  void _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    setState(() => _loading = true);
    final res = await ApiService.fetchStopArrivals(query);
    setState(() {
      _data = res;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Stop Arrivals')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      labelText: 'Stop Name',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _search,
                  child: const Text('Search'),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_loading) const Center(child: CircularProgressIndicator()),
            if (!_loading && _data != null) ...[
              ListTile(
                title: Text('Upcoming arrivals at ${_data!['stop']}', style: const TextStyle(fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 10),
              Expanded(
                child: _data!['arrivals'] == null || (_data!['arrivals'] as List).isEmpty
                    ? const Center(child: Text('No upcoming arrivals found.'))
                    : ListView.builder(
                        itemCount: (_data!['arrivals'] as List).length,
                        itemBuilder: (context, idx) {
                          final arr = _data!['arrivals'][idx];
                          return Card(
                            margin: const EdgeInsets.symmetric(vertical: 4),
                            child: ListTile(
                              leading: const Icon(Icons.directions_bus, color: Colors.teal),
                              title: Text('Route ${arr['route']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                              trailing: Text(arr['time'].toString(), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.teal)),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 4. Weather Report View
// ─────────────────────────────────────────────────────────────
class WeatherReportView extends StatefulWidget {
  const WeatherReportView({super.key});

  @override
  State<WeatherReportView> createState() => _WeatherReportViewState();
}

class _WeatherReportViewState extends State<WeatherReportView> {
  Map<String, dynamic>? _report;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  void _fetchWeather() async {
    final res = await ApiService.fetchWeatherReport(12.9716, 77.5946, 'Bengaluru');
    if (mounted) {
      setState(() {
        _report = res;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    return Scaffold(
      appBar: AppBar(title: const Text('Weather Report')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _report == null
                ? const Center(child: Text('Failed to load weather forecast.'))
                : Column(
                    children: [
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF6366F1), Color(0xFF3B82F6)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Column(
                          children: [
                            const Icon(Icons.wb_cloudy_outlined, color: Colors.white, size: 48),
                            const SizedBox(height: 10),
                            Text(
                              '${_report!['temp']}°C',
                              style: const TextStyle(fontSize: 44, fontWeight: FontWeight.bold, color: Colors.white),
                            ),
                            Text(
                              _report!['status'] ?? 'Clear',
                              style: TextStyle(fontSize: 18, color: Colors.white.withOpacity(0.9)),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              'Location: ${_report!['location']}',
                              style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.6)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      GridView.count(
                        shrinkWrap: true,
                        crossAxisCount: 2,
                        crossAxisSpacing: 10,
                        mainAxisSpacing: 10,
                        childAspectRatio: 2.2,
                        physics: const NeverScrollableScrollPhysics(),
                        children: [
                          _buildWeatherCard('Max Temperature', '${_report!['temp_max']}°C', isDark, cardBgColor),
                          _buildWeatherCard('Min Temperature', '${_report!['temp_min']}°C', isDark, cardBgColor),
                          _buildWeatherCard('Humidity', '${_report!['humidity']}%', isDark, cardBgColor),
                          _buildWeatherCard('Rain Probability', '${_report!['rain_probability']}%', isDark, cardBgColor),
                        ],
                      ),
                    ],
                  ),
      ),
    );
  }

  Widget _buildWeatherCard(String label, String value, bool isDark, Color cardBg) {
    return Card(
      color: cardBg,
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 5. Fare Calculator View
// ─────────────────────────────────────────────────────────────
class FareCalculatorView extends StatefulWidget {
  const FareCalculatorView({super.key});

  @override
  State<FareCalculatorView> createState() => _FareCalculatorViewState();
}

class _FareCalculatorViewState extends State<FareCalculatorView> {
  final _formKey = GlobalKey<FormState>();
  final _srcController = TextEditingController(text: 'Majestic');
  final _dstController = TextEditingController(text: 'Silk Board');
  Map<String, dynamic>? _results;
  bool _loading = false;
  String? _error;

  void _calculate() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _error = null;
      _results = null;
    });

    final res = await ApiService.compareRoutes(
      source: _srcController.text.trim(),
      destination: _dstController.text.trim(),
    );

    setState(() {
      _loading = false;
      if (res != null) {
        _results = res;
      } else {
        _error = 'Failed to fetch fare calculations.';
      }
    });
  }

  String _getLabelForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return 'BMTC Ordinary';
      case 'metro':
        return 'Namma Metro Standard';
      case 'multimodal':
        return 'Bus & Metro Multimodal';
      case 'bike':
        return 'Personal Bike';
      case 'car':
        return 'Personal Car';
      case 'rapido':
        return 'Rapido Two-Wheeler';
      case 'ola':
        return 'Ola Cab';
      case 'uber':
        return 'Uber Taxi';
      default:
        return mode.toUpperCase();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    return Scaffold(
      appBar: AppBar(title: const Text('Fare Calculator')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Card(
              color: cardBgColor,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      TextFormField(
                        controller: _srcController,
                        decoration: const InputDecoration(labelText: 'From Stop'),
                        validator: (v) => v!.isEmpty ? 'Enter starting stop' : null,
                      ),
                      const SizedBox(height: 10),
                      TextFormField(
                        controller: _dstController,
                        decoration: const InputDecoration(labelText: 'To Stop'),
                        validator: (v) => v!.isEmpty ? 'Enter destination stop' : null,
                      ),
                      const SizedBox(height: 14),
                      ElevatedButton(
                        onPressed: _calculate,
                        child: const Text('Calculate Fares'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            if (_loading) const Center(child: CircularProgressIndicator()),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            if (!_loading && _results != null) ...[
              const Align(
                alignment: Alignment.centerLeft,
                child: Text('💵 Estimated Cost Summary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 10),
              Table(
                border: TableBorder.all(color: Colors.grey.shade400.withOpacity(0.3), width: 1, borderRadius: BorderRadius.circular(8)),
                columnWidths: const {
                  0: FlexColumnWidth(2),
                  1: FlexColumnWidth(1),
                },
                children: [
                  const TableRow(
                    decoration: BoxDecoration(color: Colors.grey),
                    children: [
                      Padding(padding: EdgeInsets.all(10), child: Text('Travel Mode', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white))),
                      Padding(padding: EdgeInsets.all(10), child: Text('Fare Cost', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white))),
                    ],
                  ),
                  ...((_results!['modes'] as List<dynamic>).map((opt) {
                    final mode = opt['mode']?.toString() ?? '';
                    final cost = opt['cost'] ?? 0;
                    return TableRow(
                      children: [
                        Padding(padding: const EdgeInsets.all(10), child: Text(_getLabelForMode(mode))),
                        Padding(padding: const EdgeInsets.all(10), child: Text('₹$cost', style: const TextStyle(fontWeight: FontWeight.bold))),
                      ],
                    );
                  })),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
