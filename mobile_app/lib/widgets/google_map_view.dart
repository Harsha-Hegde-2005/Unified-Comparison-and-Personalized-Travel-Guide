import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../theme.dart';

enum GoogleMapStyle { roadmap, traffic, satellite, terrain }

class GoogleMapView extends StatefulWidget {
  final List<ll.LatLng> points;
  final ll.LatLng? srcPoint;
  final ll.LatLng? dstPoint;
  final ll.LatLng? liveGpsPoint;
  final double? liveGpsProgress;
  final GoogleMapStyle style;
  final Color routeColor;
  final String? startTitle;
  final String? endTitle;
  final double height;
  final bool interactive;

  const GoogleMapView({
    super.key,
    required this.points,
    this.srcPoint,
    this.dstPoint,
    this.liveGpsPoint,
    this.liveGpsProgress,
    this.style = GoogleMapStyle.roadmap,
    this.routeColor = AppTheme.bmtcColor,
    this.startTitle,
    this.endTitle,
    this.height = 220,
    this.interactive = true,
  });

  @override
  State<GoogleMapView> createState() => _GoogleMapViewState();
}

class _GoogleMapViewState extends State<GoogleMapView> {
  late fm.MapController _mapController;

  @override
  void initState() {
    super.initState();
    _mapController = fm.MapController();
  }

  @override
  void didUpdateWidget(covariant GoogleMapView oldWidget) {
    super.didUpdateWidget(oldWidget);
    final allPoints = <ll.LatLng>[];
    allPoints.addAll(widget.points);
    if (widget.srcPoint != null) allPoints.add(widget.srcPoint!);
    if (widget.dstPoint != null) allPoints.add(widget.dstPoint!);
    if (widget.liveGpsPoint != null) allPoints.add(widget.liveGpsPoint!);

    if (allPoints.length >= 2) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        try {
          final bounds = fm.LatLngBounds.fromPoints(allPoints);
          _mapController.fitCamera(
            fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(32)),
          );
        } catch (_) {}
      });
    }
  }

  String _getGoogleTileUrl() {
    switch (widget.style) {
      case GoogleMapStyle.satellite:
        return 'https://mt1.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}';
      case GoogleMapStyle.terrain:
        return 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}';
      case GoogleMapStyle.traffic:
        return 'https://mt1.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}';
      case GoogleMapStyle.roadmap:
        return 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = AppTheme.getBorder(isDark);

    ll.LatLng initialCenter = const ll.LatLng(12.9716, 77.5946);
    if (widget.liveGpsPoint != null) {
      initialCenter = widget.liveGpsPoint!;
    } else if (widget.srcPoint != null) {
      initialCenter = widget.srcPoint!;
    } else if (widget.points.isNotEmpty) {
      initialCenter = widget.points.first;
    }

    final markers = <fm.Marker>[];

    // Source Pin (Green)
    final src = widget.srcPoint ?? (widget.points.isNotEmpty ? widget.points.first : null);
    if (src != null) {
      markers.add(
        fm.Marker(
          point: src,
          width: 32,
          height: 32,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.green,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
              boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
            ),
            child: const Icon(Icons.trip_origin_rounded, color: Colors.white, size: 16),
          ),
        ),
      );
    }

    // Destination Pin (Red)
    final dst = widget.dstPoint ?? (widget.points.length > 1 ? widget.points.last : null);
    if (dst != null && dst != src) {
      markers.add(
        fm.Marker(
          point: dst,
          width: 32,
          height: 32,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.red,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
              boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
            ),
            child: const Icon(Icons.location_on_rounded, color: Colors.white, size: 18),
          ),
        ),
      );
    }

    // Live GPS Marker (Blue pulsing)
    if (widget.liveGpsPoint != null) {
      markers.add(
        fm.Marker(
          point: widget.liveGpsPoint!,
          width: 36,
          height: 36,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.blue,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2.5),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.blue.withValues(alpha: 0.5),
                  blurRadius: 10,
                  spreadRadius: 3,
                )
              ],
            ),
            child: const Icon(Icons.navigation_rounded, color: Colors.white, size: 18),
          ),
        ),
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Container(
        height: widget.height,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderCol),
        ),
        child: Stack(
          children: [
            fm.FlutterMap(
              mapController: _mapController,
              options: fm.MapOptions(
                initialCenter: initialCenter,
                initialZoom: 13.0,
                interactionOptions: fm.InteractionOptions(
                  flags: widget.interactive ? fm.InteractiveFlag.all : fm.InteractiveFlag.none,
                ),
              ),
              children: [
                fm.TileLayer(
                  urlTemplate: _getGoogleTileUrl(),
                  userAgentPackageName: 'com.google.maps.bmtc',
                ),
                if (widget.points.length >= 2)
                  fm.PolylineLayer(
                    polylines: [
                      fm.Polyline(
                        points: widget.points,
                        strokeWidth: 5.0,
                        color: widget.routeColor,
                      ),
                    ],
                  ),
                if (markers.isNotEmpty) fm.MarkerLayer(markers: markers),
              ],
            ),

            // Google Maps Branding Badge
            Positioned(
              bottom: 8,
              left: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: cardBg.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: borderCol),
                  boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Image.network(
                      'https://upload.wikimedia.org/wikipedia/commons/3/39/Google_Maps_icon_%282020%29.svg',
                      width: 14,
                      height: 14,
                      errorBuilder: (ctx, err, st) => const Icon(Icons.map_rounded, size: 14, color: AppTheme.blue),
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      'Google Maps',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.2),
                    ),
                  ],
                ),
              ),
            ),

            // Live Navigation % Progress Indicator Bar
            if (widget.liveGpsProgress != null)
              Positioned(
                top: 8,
                left: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: cardBg.withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: borderCol),
                    boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 6)],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.navigation_rounded, color: AppTheme.blue, size: 14),
                              SizedBox(width: 6),
                              Text('LIVE RIDE TRACKING', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppTheme.blue)),
                            ],
                          ),
                          Text(
                            '${widget.liveGpsProgress!.toStringAsFixed(0)}% COMPLETED',
                            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.green),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: (widget.liveGpsProgress! / 100).clamp(0.0, 1.0),
                          backgroundColor: Colors.grey.shade300,
                          color: AppTheme.green,
                          minHeight: 6,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            // Interactive Floating Zoom & Recenter Control Buttons
            if (widget.interactive)
              Positioned(
                top: 8,
                right: 8,
                child: Column(
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: cardBg.withValues(alpha: 0.95),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: borderCol),
                        boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                            padding: EdgeInsets.zero,
                            icon: const Icon(Icons.add_rounded, size: 18),
                            tooltip: 'Zoom In',
                            onPressed: () {
                              final currentZoom = _mapController.camera.zoom;
                              _mapController.move(_mapController.camera.center, currentZoom + 1.0);
                            },
                          ),
                          const Divider(height: 1, indent: 4, endIndent: 4),
                          IconButton(
                            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                            padding: EdgeInsets.zero,
                            icon: const Icon(Icons.remove_rounded, size: 18),
                            tooltip: 'Zoom Out',
                            onPressed: () {
                              final currentZoom = _mapController.camera.zoom;
                              _mapController.move(_mapController.camera.center, currentZoom - 1.0);
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 6),
                    InkWell(
                      onTap: () {
                        if (widget.srcPoint != null) {
                          _mapController.move(widget.srcPoint!, 15.0);
                        } else if (widget.points.isNotEmpty) {
                          _mapController.move(widget.points.first, 15.0);
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: cardBg.withValues(alpha: 0.95),
                          shape: BoxShape.circle,
                          border: Border.all(color: borderCol),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                        ),
                        child: const Icon(Icons.my_location_rounded, size: 16, color: AppTheme.blue),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
