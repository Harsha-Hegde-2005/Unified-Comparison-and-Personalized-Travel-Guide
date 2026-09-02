import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import 'package:google_maps_flutter/google_maps_flutter.dart' as gm;
import '../services/map_theme_service.dart';
import '../widgets/app_settings_modal.dart';

class MapScreen extends StatefulWidget {
  final ValueNotifier<String> mapStyleNotifier;
  final ValueNotifier<String> mapProviderNotifier;

  const MapScreen({
    super.key,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
  });

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  // Coords
  final ll.LatLng _centerLL = ll.LatLng(12.9716, 77.5946);
  final gm.LatLng _centerGM = const gm.LatLng(12.9716, 77.5946);

  // Google Map Controller
  gm.GoogleMapController? _googleMapController;

  // Markers
  final List<Map<String, dynamic>> _markerData = [
    {'id': 'majestic', 'title': 'Majestic Bus Station (KSR)', 'lat': 12.9716, 'lng': 77.5946},
    {'id': 'indiranagar', 'title': 'Indiranagar Metro Station', 'lat': 12.9784, 'lng': 77.6408},
    {'id': 'silkboard', 'title': 'Silk Board Junction', 'lat': 12.9176, 'lng': 77.6244},
  ];

  // Route Points
  final List<ll.LatLng> _routePointsLL = const [
    ll.LatLng(12.9716, 77.5946),
    ll.LatLng(12.9756, 77.6100),
    ll.LatLng(12.9784, 77.6408),
  ];

  final List<gm.LatLng> _routePointsGM = const [
    gm.LatLng(12.9716, 77.5946),
    gm.LatLng(12.9756, 77.6100),
    gm.LatLng(12.9784, 77.6408),
  ];

  @override
  void initState() {
    super.initState();
    widget.mapStyleNotifier.addListener(_onStyleChanged);
    widget.mapProviderNotifier.addListener(_onProviderChanged);
    MapThemeService.mapStyleNotifier.addListener(_onStyleChanged);
    MapThemeService.mapProviderNotifier.addListener(_onProviderChanged);
  }

  @override
  void dispose() {
    widget.mapStyleNotifier.removeListener(_onStyleChanged);
    widget.mapProviderNotifier.removeListener(_onProviderChanged);
    MapThemeService.mapStyleNotifier.removeListener(_onStyleChanged);
    MapThemeService.mapProviderNotifier.removeListener(_onProviderChanged);
    super.dispose();
  }

  void _onStyleChanged() {
    if (mounted) setState(() {});
  }

  void _onProviderChanged() {
    if (mounted) setState(() {});
  }

  bool _useGoogleMapsNative() {
    final isMobile = defaultTargetPlatform == TargetPlatform.android ||
        defaultTargetPlatform == TargetPlatform.iOS;
    final provider = MapThemeService.mapProvider;
    return isMobile && provider == 'google';
  }

  String _getGoogleTileUrl() {
    final style = MapThemeService.mapStyle;
    if (style == 'satellite') {
      return 'https://mt1.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}';
    }
    if (style == 'terrain') {
      return 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}';
    }
    if (style == 'dark') {
      return 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    }
    return 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
  }

  Widget _buildFlutterMap(BuildContext context) {
    final provider = MapThemeService.mapProvider;
    final style = MapThemeService.mapStyle;

    String urlTemplate = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    if (provider == 'google') {
      urlTemplate = _getGoogleTileUrl();
    } else {
      if (style == 'dark') {
        urlTemplate = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
      } else if (style == 'satellite') {
        urlTemplate = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      } else if (style == 'terrain') {
        urlTemplate = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png';
      }
    }

    final tileLayer = fm.TileLayer(
      urlTemplate: urlTemplate,
      subdomains: const ['a', 'b', 'c'],
      userAgentPackageName: 'com.bmtc.unified',
    );

    final filteredTileLayer = style == 'dark'
        ? ColorFiltered(
            colorFilter: const ColorFilter.matrix(<double>[
              -0.7, 0, 0, 0, 220,
              0, -0.7, 0, 0, 220,
              0, 0, -0.7, 0, 220,
              0, 0, 0, 1.0, 0,
            ]),
            child: tileLayer,
          )
        : tileLayer;

    return fm.FlutterMap(
      options: fm.MapOptions(
        initialCenter: _centerLL,
        initialZoom: 12.0,
      ),
      children: [
        filteredTileLayer,

        // Polylines route overlay
        fm.PolylineLayer(
          polylines: [
            fm.Polyline(
              points: _routePointsLL,
              color: const Color(0xFF7C5CFF),
              strokeWidth: 5.0,
            ),
          ],
        ),

        // Markers overlay
        fm.MarkerLayer(
          markers: _markerData.map((data) {
            return fm.Marker(
              point: ll.LatLng(data['lat'], data['lng']),
              width: 40,
              height: 40,
              child: GestureDetector(
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(data['title'])),
                  );
                },
                child: const Icon(
                  Icons.location_on,
                  color: Colors.red,
                  size: 32,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    // Create markers for Google Map
    final Set<gm.Marker> googleMarkers = _markerData.map((data) {
      return gm.Marker(
        markerId: gm.MarkerId(data['id']),
        position: gm.LatLng(data['lat'], data['lng']),
        infoWindow: gm.InfoWindow(title: data['title']),
      );
    }).toSet();

    // Create polylines for Google Map
    final Set<gm.Polyline> googlePolylines = {
      gm.Polyline(
        polylineId: const gm.PolylineId('route1'),
        points: _routePointsGM,
        color: const Color(0xFF7C5CFF),
        width: 5,
      ),
    };

    return Scaffold(
      body: Stack(
        children: [
          // Map Canvas
          Positioned.fill(
            child: _useGoogleMapsNative()
                ? gm.GoogleMap(
                    initialCameraPosition: gm.CameraPosition(target: _centerGM, zoom: 12),
                    onMapCreated: (controller) {
                      _googleMapController = controller;
                    },
                    markers: googleMarkers,
                    polylines: googlePolylines,
                    mapType: _getGoogleMapType(),
                    zoomControlsEnabled: false,
                  )
                : _buildFlutterMap(context),
          ),

          // Floating Search Bar & Controls
          Positioned(
            top: 40,
            left: 15,
            right: 15,
            child: Card(
              color: cardBgColor,
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Row(
                  children: [
                    const Icon(Icons.search, color: Colors.grey),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: TextField(
                        decoration: InputDecoration(
                          hintText: 'Search stops, routes or landmarks...',
                          border: InputBorder.none,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.my_location),
                      onPressed: () {
                        if (_useGoogleMapsNative() && _googleMapController != null) {
                          _googleMapController!.animateCamera(
                            gm.CameraUpdate.newLatLngZoom(_centerGM, 14),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Centering on Majestic Bus Depot...')),
                          );
                        }
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.settings_outlined),
                      tooltip: 'App Settings',
                      onPressed: () => showAppSettingsModal(context),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Floating Action Buttons
          Positioned(
            bottom: 20,
            right: 15,
            child: Column(
              children: [
                FloatingActionButton.small(
                  heroTag: 'zoom_in',
                  backgroundColor: cardBgColor,
                  child: const Icon(Icons.add),
                  onPressed: () {
                    if (_useGoogleMapsNative() && _googleMapController != null) {
                      _googleMapController!.animateCamera(gm.CameraUpdate.zoomIn());
                    }
                  },
                ),
                const SizedBox(height: 8),
                FloatingActionButton.small(
                  heroTag: 'zoom_out',
                  backgroundColor: cardBgColor,
                  child: const Icon(Icons.remove),
                  onPressed: () {
                    if (_useGoogleMapsNative() && _googleMapController != null) {
                      _googleMapController!.animateCamera(gm.CameraUpdate.zoomOut());
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  gm.MapType _getGoogleMapType() {
    final style = widget.mapStyleNotifier.value;
    if (style == 'satellite') return gm.MapType.satellite;
    if (style == 'terrain') return gm.MapType.terrain;
    return gm.MapType.normal;
  }
}
