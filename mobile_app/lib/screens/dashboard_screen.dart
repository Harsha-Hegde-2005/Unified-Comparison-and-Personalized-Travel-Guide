import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/modals.dart';

class DashboardScreen extends StatefulWidget {
  final ValueNotifier<ThemeMode> themeNotifier;
  final ValueNotifier<String> mapStyleNotifier;
  final ValueNotifier<String> mapProviderNotifier;
  final String username;
  final VoidCallback onOpenLogin;
  final VoidCallback onNavigateToChat;
  final VoidCallback onNavigateToMap;
  final ValueChanged<Map<String, String>> onNavigateToPlanWithRoute;
  final VoidCallback onNavigateToTransit;

  const DashboardScreen({
    super.key,
    required this.themeNotifier,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
    required this.username,
    required this.onOpenLogin,
    required this.onNavigateToChat,
    required this.onNavigateToMap,
    required this.onNavigateToPlanWithRoute,
    required this.onNavigateToTransit,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late String _timeString;
  late String _dateString;
  late Timer _timer;

  Map<String, dynamic>? _dashboardData;
  List<dynamic>? _vehicles;
  List<dynamic>? _documents;

  @override
  void initState() {
    super.initState();
    _timeString = _formatDateTime(DateTime.now(), 'hh:mm a');
    _dateString = _formatDateTime(DateTime.now(), 'EEE, MMM d, yyyy');
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => _getTime());
    _loadData();
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  void _getTime() {
    final now = DateTime.now();
    if (mounted) {
      setState(() {
        _timeString = _formatDateTime(now, 'hh:mm a');
        _dateString = _formatDateTime(now, 'EEE, MMM d, yyyy');
      });
    }
  }

  String _formatDateTime(DateTime dt, String format) => DateFormat(format).format(dt);

  String _getGreeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  Future<void> _loadData() async {
    final dashboard = await ApiService.fetchDashboard();
    final vehicles = await ApiService.fetchVehicles();
    final documents = await ApiService.fetchDocuments();

    if (mounted) {
      setState(() {
        _dashboardData = dashboard;
        _vehicles = vehicles;
        _documents = documents;
      });
    }
  }

  void _showAddVehicleDialog() {
    final nameCtrl = TextEditingController();
    String fuelType = 'Petrol';
    final effCtrl = TextEditingController(text: '15.0');

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Add Vehicle to Garage'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Vehicle Name (e.g. Honda City)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: fuelType,
                decoration: const InputDecoration(labelText: 'Fuel Type', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'Petrol', child: Text('Petrol')),
                  DropdownMenuItem(value: 'Diesel', child: Text('Diesel')),
                  DropdownMenuItem(value: 'Electric', child: Text('Electric (EV)')),
                  DropdownMenuItem(value: 'CNG', child: Text('CNG')),
                ],
                onChanged: (v) {
                  if (v != null) fuelType = v;
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: effCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Efficiency (km/l or km/kWh)', border: OutlineInputBorder()),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                final name = nameCtrl.text.trim();
                final eff = double.tryParse(effCtrl.text.trim()) ?? 14.0;
                if (name.isNotEmpty) {
                  await ApiService.addVehicle(name, fuelType, eff);
                  if (context.mounted) {
                    Navigator.pop(context);
                  }
                  _loadData();
                }
              },
              child: const Text('Add'),
            ),
          ],
        );
      },
    );
  }

  void _showSettingsBottomSheet() {
    final urlCtrl = TextEditingController(text: ApiService.baseUrl);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.getCard(isDark),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade400, borderRadius: BorderRadius.circular(2))),
              ),
              const SizedBox(height: 16),
              const Text('Application Settings', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),

              // Base URL
              const Text('Backend Server URL', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              TextField(
                controller: urlCtrl,
                decoration: InputDecoration(
                  hintText: 'http://localhost:8000',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  suffixIcon: IconButton(
                    icon: const Icon(Icons.save),
                    onPressed: () {
                      ApiService.baseUrl = urlCtrl.text.trim();
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Backend URL set to: ${ApiService.baseUrl}')),
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Theme Switcher
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Theme Mode', style: TextStyle(fontWeight: FontWeight.bold)),
                  SegmentedButton<ThemeMode>(
                    segments: const [
                      ButtonSegment(value: ThemeMode.light, icon: Icon(Icons.light_mode_rounded), label: Text('Light')),
                      ButtonSegment(value: ThemeMode.dark, icon: Icon(Icons.dark_mode_rounded), label: Text('Dark')),
                    ],
                    selected: {widget.themeNotifier.value},
                    onSelectionChanged: (set) {
                      widget.themeNotifier.value = set.first;
                    },
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final journeys = _dashboardData?['saved_journeys'] as List<dynamic>? ?? [];
    final totalCO2 = _dashboardData?['total_co2_saved'] ?? 42.5;
    final trees = (totalCO2 / 20.0).toStringAsFixed(1);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bengaluru Commuter', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded),
            tooltip: 'Toggle Theme',
            onPressed: () {
              widget.themeNotifier.value = isDark ? ThemeMode.light : ThemeMode.dark;
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings',
            onPressed: _showSettingsBottomSheet,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 28),
          children: [
            // 0. Account Profile Bar (Database Sync)
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 14,
                        backgroundColor: widget.username != 'Guest'
                            ? AppTheme.green.withValues(alpha: 0.2)
                            : Colors.grey.withValues(alpha: 0.2),
                        child: Icon(
                          widget.username != 'Guest' ? Icons.person_rounded : Icons.person_outline_rounded,
                          size: 16,
                          color: widget.username != 'Guest' ? AppTheme.green : mutedColor,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.username != 'Guest' ? widget.username : 'Guest User',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor),
                          ),
                          Text(
                            widget.username != 'Guest' ? 'Synced with Transit DB' : 'Not signed in',
                            style: TextStyle(fontSize: 10, color: mutedColor),
                          ),
                        ],
                      ),
                    ],
                  ),
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      visualDensity: VisualDensity.compact,
                    ),
                    onPressed: widget.onOpenLogin,
                    icon: Icon(
                      widget.username != 'Guest' ? Icons.logout_rounded : Icons.login_rounded,
                      size: 14,
                      color: widget.username != 'Guest' ? AppTheme.red : AppTheme.bmtcColor,
                    ),
                    label: Text(
                      widget.username != 'Guest' ? 'Log Out' : 'Sign In / Register',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: widget.username != 'Guest' ? AppTheme.red : AppTheme.bmtcColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 1. Hero Greeting Banner
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7C3AED), Color(0xFF5B21B6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _getGreeting(),
                        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          _timeString,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(_dateString, style: const TextStyle(color: Colors.white70, fontSize: 12)),
                  const SizedBox(height: 14),

                  // Quick search action
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF7C3AED),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      elevation: 0,
                    ),
                    onPressed: () {
                      widget.onNavigateToPlanWithRoute({});
                    },
                    icon: const Icon(Icons.directions_rounded, size: 18),
                    label: const Text('Plan New Journey', style: TextStyle(fontWeight: FontWeight.w800)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 2. Eco Impact & Carbon Savings Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.green.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.eco_rounded, color: AppTheme.green, size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Eco Impact & Sustainability', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: textColor)),
                        const SizedBox(height: 4),
                        Text('Saved $totalCO2 kg CO2 (~$trees trees equivalent) by choosing public transit!',
                            style: TextStyle(fontSize: 12, color: mutedColor, height: 1.3)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 3. Quick Transit Tools Grid
            Text('QUICK TRANSIT TOOLS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 10),
            GridView.count(
              crossAxisCount: 3,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _buildToolTile('Route Lookup', Icons.alt_route_rounded, AppTheme.bmtcColor, isDark, widget.onNavigateToTransit),
                _buildToolTile('Timetables', Icons.schedule_rounded, AppTheme.metroColor, isDark, widget.onNavigateToTransit),
                _buildToolTile('Stops Info', Icons.pin_drop_rounded, AppTheme.blue, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const StopsInfoModal());
                }),
                _buildToolTile('Fare Calc', Icons.calculate_outlined, AppTheme.carColor, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const FareCalculatorModal());
                }),
                _buildToolTile('Weather', Icons.wb_sunny_outlined, Colors.amber, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const WeatherReportModal());
                }),
                _buildToolTile('Fare Guide', Icons.menu_book_rounded, AppTheme.multimodalColor, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const FareGuideModal());
                }),
              ],
            ),
            const SizedBox(height: 20),

            // 4. Saved Journeys
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('SAVED JOURNEYS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                if (journeys.isNotEmpty)
                  Text('${journeys.length} Saved', style: TextStyle(fontSize: 11, color: mutedColor)),
              ],
            ),
            const SizedBox(height: 10),

            if (journeys.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Center(
                  child: Text('No saved journeys yet. Save your favorite routes from search!', style: TextStyle(fontSize: 12, color: mutedColor)),
                ),
              )
            else
              ...journeys.map((j) {
                final from = j['from_stop'] ?? j['from'] ?? 'Majestic';
                final to = j['to_stop'] ?? j['to'] ?? 'Indiranagar';
                final mode = j['mode'] ?? 'bmtc';
                final customName = j['custom_name'] ?? '$from ➔ $to';
                final cost = j['cost'] ?? 0;
                final dur = j['duration'] ?? 0;

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppTheme.getModeColor(mode).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(AppTheme.getModeIcon(mode), color: AppTheme.getModeColor(mode), size: 18),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(customName.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor)),
                            Text('$from ➔ $to · ₹$cost · $dur min', style: TextStyle(fontSize: 11, color: mutedColor)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                        color: AppTheme.getAccent(isDark),
                        onPressed: () {
                          widget.onNavigateToPlanWithRoute({'source': from.toString(), 'destination': to.toString()});
                        },
                      ),
                    ],
                  ),
                );
              }),
            const SizedBox(height: 20),

            // 5. User Garage (Personal Vehicles)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('MY GARAGE (VEHICLES)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                TextButton.icon(
                  onPressed: _showAddVehicleDialog,
                  icon: const Icon(Icons.add, size: 14),
                  label: const Text('Add Vehicle', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 6),

            if (_vehicles == null || _vehicles!.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.directions_car_filled_rounded, color: AppTheme.carColor),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text('Add your car or two-wheeler to get exact fuel & parking estimates in journey comparisons.',
                          style: TextStyle(fontSize: 12, color: mutedColor)),
                    ),
                  ],
                ),
              )
            else
              ..._vehicles!.map((v) {
                final vId = v['id'];
                final vName = v['name'] ?? 'Car';
                final vFuel = v['fuel_type'] ?? 'Petrol';
                final vEff = v['efficiency'] ?? 15.0;

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.directions_car_rounded, color: AppTheme.carColor),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(vName.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor)),
                            Text('$vFuel · $vEff km/l', style: TextStyle(fontSize: 11, color: mutedColor)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline, size: 18, color: Colors.grey),
                        onPressed: () async {
                          if (vId != null) {
                            await ApiService.deleteVehicle(vId as int);
                            _loadData();
                          }
                        },
                      ),
                    ],
                  ),
                );
              }),
            const SizedBox(height: 20),

            // 6. Glovebox (Document Vault)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('MY GLOVEBOX (DOCUMENTS)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                if (_documents != null && _documents!.isNotEmpty)
                  Text('${_documents!.length} Stored', style: TextStyle(fontSize: 11, color: mutedColor)),
              ],
            ),
            const SizedBox(height: 6),

            if (_documents == null || _documents!.isEmpty)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.folder_shared_outlined, color: Color(0xFF7C3AED)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text('Digital document vault ready for DL, RC, bus passes, and vehicle insurance.',
                          style: TextStyle(fontSize: 12, color: mutedColor)),
                    ),
                  ],
                ),
              )
            else
              ..._documents!.map((d) {
                final dName = d['name'] ?? d['document_type'] ?? 'Document';
                return Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.description_rounded, size: 18, color: Color(0xFF7C3AED)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(dName.toString(), style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: textColor)),
                      ),
                      const PillBadge(text: 'SECURE', color: AppTheme.green, isSmall: true),
                    ],
                  ),
                );
              }),
            const SizedBox(height: 20),

            // 7. Popular Transit Hubs in Bengaluru
            Text('POPULAR BENGALURU HUBS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildHubChip('Majestic (KBS)', 'Majestic', textColor, cardBg, isDark),
                _buildHubChip('Indiranagar 100ft', 'Indiranagar', textColor, cardBg, isDark),
                _buildHubChip('Whitefield ITPL', 'Whitefield', textColor, cardBg, isDark),
                _buildHubChip('Electronic City Phase 1', 'Electronic City', textColor, cardBg, isDark),
                _buildHubChip('Silk Board Junction', 'Silk Board', textColor, cardBg, isDark),
                _buildHubChip('Kempegowda Airport', 'Kempegowda International Airport', textColor, cardBg, isDark),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildToolTile(String title, IconData icon, Color color, bool isDark, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: isDark ? 0.12 : 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 6),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHubChip(String label, String dest, Color textColor, Color cardBg, bool isDark) {
    return ActionChip(
      backgroundColor: cardBg,
      side: BorderSide(color: AppTheme.getBorder(isDark)),
      avatar: const Icon(Icons.place_rounded, size: 14, color: AppTheme.bmtcColor),
      label: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor)),
      onPressed: () {
        widget.onNavigateToPlanWithRoute({'destination': dest});
      },
    );
  }
}
