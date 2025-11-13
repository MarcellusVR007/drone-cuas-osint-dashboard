const { createApp, ref, reactive, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        // State
        const currentView = ref('dashboard');
        const loading = ref(false);
        const stats = reactive({
            summary: {},
            top_drone_types: [],
            top_targeted_areas: [],
            interventions_by_type: [],
            purposes_detected: []
        });

        const incidents = ref([]);
        const droneTypes = ref([]);
        const restrictedAreas = ref([]);
        const patterns = ref([]);
        const interventionEffectiveness = ref([]);
        const interventionStats = ref({});
        const dataSources = ref([]);
        const selectedIncident = ref(null);
        const selectedSource = ref(null);

        // Sort state
        const sortColumn = ref('date');
        const sortDirection = ref('desc');

        let map = null;
        let detailMap = null;

        // Computed
        const filteredIncidents = computed(() => incidents.value.slice(0, 20));

        // Initialize data on component mount
        onMounted(async () => {
            await fetchStats();
            await fetchIncidents();
        });

        // Helper function to convert source code to full name
        const getSourceName = (sourceCode) => {
            const sourceMap = {
                'senhive': 'Senhive (Drone Detection)',
                'bbc_monitoring': 'BBC Monitoring (OSINT)',
                'janes_ihs': 'Janes Intelligence (Military DB)',
                'reuters_news': 'Reuters News',
                'military_aviation_forums': 'Military Aviation Forums',
                'adsb_exchange': 'ADS-B Exchange',
                'dutch_mil_intel': 'Dutch Ministry of Defence',
                'belgian_mil_intel': 'Belgian Ministry of Defence',
                'twitter_osint': 'Twitter/X OSINT',
                'flightradar24': 'FlightRadar24',
                'nato_air_ops': 'NATO Early Warning',
                'citizen_submissions': 'Citizen Submissions'
            };
            return sourceMap[sourceCode] || sourceCode;
        };

        // Helper functions (needed by sortIncidents)
        const getLocationName = (restrictedAreaId) => {
            if (!restrictedAreaId) return 'Unknown location';
            const area = restrictedAreas.value.find(a => a.id === restrictedAreaId);
            return area ? area.name : 'Unknown location';
        };

        const getCountryFromArea = (restrictedAreaId) => {
            if (!restrictedAreaId) return 'N/A';
            const area = restrictedAreas.value.find(a => a.id === restrictedAreaId);
            return area ? area.country : 'N/A';
        };

        // Methods
        const fetchStats = async () => {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                Object.assign(stats, data);
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        };

        const sortIncidents = (incidentsList) => {
            const sorted = [...incidentsList].sort((a, b) => {
                let valA, valB;
                const direction = sortDirection.value === 'asc' ? 1 : -1;

                switch (sortColumn.value) {
                    case 'date':
                        valA = new Date(a.sighting_date);
                        valB = new Date(b.sighting_date);
                        return (valA - valB) * direction;

                    case 'location':
                        valA = getLocationName(a.restricted_area_id).toLowerCase();
                        valB = getLocationName(b.restricted_area_id).toLowerCase();
                        return valA.localeCompare(valB) * direction;

                    case 'country':
                        valA = getCountryFromArea(a.restricted_area_id);
                        valB = getCountryFromArea(b.restricted_area_id);
                        return valA.localeCompare(valB) * direction;

                    case 'drone':
                        valA = (a.drone_description || 'N/A').toLowerCase();
                        valB = (b.drone_description || 'N/A').toLowerCase();
                        return valA.localeCompare(valB) * direction;

                    case 'source':
                        valA = (a.display_source || '').toLowerCase();
                        valB = (b.display_source || '').toLowerCase();
                        return valA.localeCompare(valB) * direction;

                    case 'purpose':
                        valA = (a.purpose_assessment || 'Unknown').toLowerCase();
                        valB = (b.purpose_assessment || 'Unknown').toLowerCase();
                        return valA.localeCompare(valB) * direction;

                    case 'confidence':
                        valA = a.confidence_score || 0;
                        valB = b.confidence_score || 0;
                        return (valA - valB) * direction;

                    default:
                        return 0;
                }
            });

            return sorted;
        };

        const sortBy = (column) => {
            if (sortColumn.value === column) {
                // Toggle direction
                sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
            } else {
                // New column, default to descending (most recent/highest first)
                sortColumn.value = column;
                sortDirection.value = 'desc';
            }

            // Re-sort incidents
            incidents.value = sortIncidents(incidents.value);
        };

        const getSortClass = (column) => {
            if (sortColumn.value === column) {
                return sortDirection.value;
            }
            return '';
        };

        const fetchIncidents = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/incidents/?limit=100');
                const data = await response.json();

                // Filter: only last 60 days
                const sixtyDaysAgo = new Date();
                sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);

                const recentIncidents = (data.incidents || []).filter(inc => {
                    const incDate = new Date(inc.sighting_date);
                    return incDate >= sixtyDaysAgo;
                });

                // Set default sort: most recent first
                sortColumn.value = 'date';
                sortDirection.value = 'desc';
                incidents.value = sortIncidents(recentIncidents);
                // Also fetch restricted areas for location name lookup
                if (restrictedAreas.value.length === 0) {
                    await fetchRestrictedAreas();
                }
                // Fetch data sources
                if (dataSources.value.length === 0) {
                    await fetchDataSources();
                }
            } catch (error) {
                console.error('Error fetching incidents:', error);
            } finally {
                loading.value = false;
            }
        };

        const fetchDataSources = async () => {
            try {
                const response = await fetch('/api/data-sources/');
                const data = await response.json();
                dataSources.value = data.sources || [];
            } catch (error) {
                console.error('Error fetching data sources:', error);
            }
        };

        const viewSourceDetail = (sourceType) => {
            // Map incident source type to data source
            const sourceMap = {
                'authority': dataSources.value.filter(s => s.source_type === 'authority'),
                'api': dataSources.value.filter(s => ['drone_detection', 'adsb'].includes(s.source_type)),
                'news': dataSources.value.filter(s => s.source_type === 'news'),
                'submission': dataSources.value.filter(s => s.source_type === 'submission'),
                'intelligence': dataSources.value.filter(s => s.source_type === 'sigint')
            };

            const sources = sourceMap[sourceType] || [];

            let html = `<div class="row mb-3">`;

            if (sources.length === 0) {
                html += `<div class="col-md-12"><div class="alert alert-warning">No sources found for type: ${sourceType}</div></div>`;
            } else {
                sources.forEach(source => {
                    const scoreColor = source.combined_score >= 0.8 ? 'success' : source.combined_score >= 0.6 ? 'warning' : 'danger';
                    html += `
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-header bg-primary">
                                    <strong>${source.name}</strong>
                                </div>
                                <div class="card-body">
                                    <p><strong>Type:</strong> <span class="badge badge-info">${source.source_type}</span></p>
                                    <p><strong>Verification Status:</strong> <span class="badge badge-${source.verification_status === 'high_confidence' ? 'danger' : source.verification_status === 'verified' ? 'success' : source.verification_status === 'partial' ? 'warning' : 'secondary'}">${source.verification_status}</span></p>
                                    <hr>
                                    <p><strong>Reliability:</strong> <span class="badge badge-info">${(source.reliability_score * 100).toFixed(0)}%</span></p>
                                    <p><strong>Freshness:</strong> <span class="badge badge-info">${(source.freshness_score * 100).toFixed(0)}%</span></p>
                                    <p><strong>Coverage:</strong> <span class="badge badge-info">${(source.coverage_score * 100).toFixed(0)}%</span></p>
                                    <p><strong>Data Quality:</strong> <span class="badge badge-info">${(source.data_quality_score * 100).toFixed(0)}%</span></p>
                                    <p><strong>Combined Score:</strong> <span class="badge badge-${scoreColor}">${(source.combined_score * 100).toFixed(0)}%</span></p>
                                    <hr>
                                    <p><strong>Capabilities:</strong></p>
                                    <div>
                                        ${(source.capabilities || []).map(cap => `<span class="badge badge-secondary me-2">${cap}</span>`).join('')}
                                    </div>
                                    ${source.coverage_regions && source.coverage_regions.length > 0 ? `
                                        <p class="mt-2"><strong>Coverage Regions:</strong> ${source.coverage_regions.join(', ')}</p>
                                    ` : ''}
                                    ${source.url ? `
                                        <p class="mt-2"><a href="${source.url}" target="_blank" class="btn btn-sm btn-outline-primary">Visit Website <i class="fas fa-external-link-alt"></i></a></p>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                });
            }

            html += `</div>`;

            document.getElementById('sourceContent').innerHTML = html;

            setTimeout(() => {
                try {
                    if (typeof bootstrap !== 'undefined') {
                        const modalElement = document.getElementById('sourceModal');
                        const modal = new bootstrap.Modal(modalElement);
                        modal.show();
                    }
                } catch (error) {
                    console.error('Error showing source modal:', error);
                }
            }, 150);
        };

        const fetchDroneTypes = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/drone-types/?limit=100');
                const data = await response.json();
                droneTypes.value = data.drone_types || [];
            } catch (error) {
                console.error('Error fetching drone types:', error);
            } finally {
                loading.value = false;
            }
        };

        const fetchRestrictedAreas = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/restricted-areas/?limit=100');
                const data = await response.json();
                restrictedAreas.value = data.restricted_areas || [];
                initMap();
            } catch (error) {
                console.error('Error fetching restricted areas:', error);
            } finally {
                loading.value = false;
            }
        };

        const fetchPatterns = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/patterns/?limit=100');
                const data = await response.json();
                patterns.value = data.patterns || [];
            } catch (error) {
                console.error('Error fetching patterns:', error);
            } finally {
                loading.value = false;
            }
        };

        const fetchInterventions = async () => {
            loading.value = true;
            try {
                // Fetch effectiveness data
                const effResponse = await fetch('/api/interventions/analysis/effectiveness');
                interventionEffectiveness.value = await effResponse.json();

                // Get summary stats
                const totalResponse = await fetch('/api/interventions/?limit=1');
                const totalData = await totalResponse.json();
                const total = totalData.total || 0;

                const successCount = interventionEffectiveness.value.reduce((sum, item) => sum + item.successful, 0);
                const successRate = total > 0 ? ((successCount / total) * 100).toFixed(1) : 0;

                interventionStats.value = {
                    total: total,
                    successful: successCount,
                    success_rate: successRate
                };
            } catch (error) {
                console.error('Error fetching interventions:', error);
            } finally {
                loading.value = false;
            }
        };

        const viewIncident = async (id) => {
            // Fetch full incident details including source_url and secondary_sources
            let incident;
            try {
                const response = await fetch(`/api/incidents/${id}`);
                incident = await response.json();
                if (!incident) return;

                selectedIncident.value = incident;
            } catch (error) {
                console.error('Error fetching incident details:', error);
                return;
            }

            // Build the HTML content for the modal
            const locationName = getLocationName(incident.restricted_area_id);
            const area = restrictedAreas.value.find(a => a.id === incident.restricted_area_id);
            const droneType = droneTypes.value.find(d => d.id === incident.drone_type_id);

            // Build evidence explanation
            let evidenceExplanation = '';
            if (incident.identification_evidence) {
                evidenceExplanation = `
                    <div class="alert alert-info">
                        <strong><i class="fas fa-magnifying-glass"></i> Evidence & Reasoning:</strong>
                        <p>${incident.identification_evidence}</p>
                    </div>
                `;
            }

            // Build drone characteristics explanation
            let characteristicsExplanation = '';
            if (incident.drone_characteristics) {
                characteristicsExplanation = `
                    <div class="alert alert-warning">
                        <strong><i class="fas fa-info-circle"></i> Observed Characteristics:</strong>
                        <p>${incident.drone_characteristics}</p>
                        <small class="text-muted">Sources: ${incident.drone_characteristics_sources || 'Multiple observers'}</small>
                    </div>
                `;
            }

            // Build identification method explanation
            let identificationExplanation = '';
            const identMethodLabel = {
                'signals': 'Signals Intelligence (SIGINT)',
                'radar': 'Radar Detection',
                'video': 'Video Analysis',
                'photo': 'Photographic Analysis',
                'recovered_wreckage': 'Recovered Wreckage Analysis',
                'visual': 'Visual Observation',
                'adsb': 'ADS-B Tracking'
            };

            if (incident.identification_method) {
                identificationExplanation = `
                    <div class="card mb-3">
                        <div class="card-header bg-secondary">
                            <strong>Identification Method: ${identMethodLabel[incident.identification_method] || incident.identification_method}</strong>
                        </div>
                        <div class="card-body">
                            <p>Identified by: <strong>${incident.identified_by || 'Unknown'}</strong></p>
                            <p>Confidence Level: <strong>${(incident.identification_confidence * 100).toFixed(0)}%</strong></p>
                            ${evidenceExplanation}
                        </div>
                    </div>
                `;
            }

            const html = `
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-danger">
                                <strong>Incident Summary</strong>
                            </div>
                            <div class="card-body">
                                <p><strong>Title:</strong> ${incident.title}</p>
                                <p><strong>Description:</strong> ${incident.description || 'N/A'}</p>
                                <p><strong>Sighting Date:</strong> ${formatDate(incident.sighting_date)} at ${incident.sighting_time || 'Unknown time'}</p>
                                <p><strong>Report Date:</strong> ${formatDate(incident.report_date)}</p>
                                <p><strong>Location:</strong> ${locationName}${area ? ', ' + area.country : ''}</p>
                                <p><strong>Confidence Score:</strong>
                                    <span class="badge badge-danger">${(incident.confidence_score * 100).toFixed(0)}%</span>
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-secondary">
                                <strong>Source & Verification</strong>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <h6><strong>Reporting Source Hierarchy</strong></h6>

                                    <!-- Primary Source -->
                                    <div class="card bg-dark border-success mb-2">
                                        <div class="card-header bg-success text-dark py-2">
                                            <strong>📊 Primary Source</strong>
                                            ${incident.primary_source_credibility ? `<span class="badge bg-warning text-dark float-end">Credibility: ${incident.primary_source_credibility}/10</span>` : ''}
                                        </div>
                                        <div class="card-body py-2">
                                            <p class="mb-1"><strong>${incident.primary_source_name || getSourceName(incident.source)}</strong></p>
                                            ${incident.source_url ?
                                                `<a href="${incident.source_url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-success">🔗 View Original Report</a>`
                                                : '<small class="text-muted">No source URL available</small>'}
                                        </div>
                                    </div>

                                    <!-- Secondary Sources if available -->
                                    ${(() => {
                                        try {
                                            const secondarySources = Array.isArray(incident.secondary_sources) ? incident.secondary_sources : [];
                                            if (secondarySources.length > 0) {
                                                return `
                                                    <div class="card bg-dark border-info mb-2">
                                                        <div class="card-header bg-info text-dark py-2">
                                                            <strong>📰 Also Reported By</strong>
                                                        </div>
                                                        <div class="card-body py-2">
                                                            ${secondarySources.map(source => `
                                                                <div class="mb-2">
                                                                    <p class="mb-1"><small>${source.name || 'Unknown'}</small></p>
                                                                    ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-info">View</a>` : ''}
                                                                    ${source.credibility ? `<span class="badge bg-secondary">Credibility: ${source.credibility}/10</span>` : ''}
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    </div>
                                                `;
                                            }
                                            return '';
                                        } catch (e) {
                                            return '';
                                        }
                                    })()}

                                    <div class="mt-2">
                                        <small class="text-muted">Report Confidence: <strong>${(incident.confidence_score * 100).toFixed(0)}%</strong></small>
                                    </div>
                                </div>

                                <hr class="bg-secondary">

                                <p><strong>Suspected Operator:</strong> ${incident.suspected_operator || 'Unknown'}</p>
                                <p><strong>Purpose Assessment:</strong> ${incident.purpose_assessment || 'Unknown'}</p>
                                <p><strong>Altitude:</strong> ${incident.altitude_m || 'Unknown'} meters</p>
                                <p><strong>Duration:</strong> ${incident.duration_minutes || 'Unknown'} minutes</p>
                                <p><strong>Distance to Restricted Area:</strong> ${incident.distance_to_restricted_m || 'Unknown'} meters</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-12">
                        ${identificationExplanation}
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-12">
                        ${characteristicsExplanation}
                    </div>
                </div>

                ${area ? `
                <div class="card mb-4">
                    <div class="card-header bg-info">
                        <strong>Restricted Area Details</strong>
                    </div>
                    <div class="card-body">
                        <p><strong>Area Name:</strong> ${area.name}</p>
                        <p><strong>Type:</strong> ${area.area_type}</p>
                        <p><strong>Country:</strong> ${area.country}</p>
                        <p><strong>Threat Level:</strong> <span class="badge badge-danger">${area.threat_level}/5</span></p>
                        <p><strong>Coordinates:</strong> ${area.latitude}, ${area.longitude}</p>
                        <p><strong>Description:</strong> ${area.description || 'N/A'}</p>
                    </div>
                </div>
                ` : ''}

                ${droneType ? `
                <div class="card mb-4">
                    <div class="card-header bg-success">
                        <strong>Identified Drone Type Details</strong>
                    </div>
                    <div class="card-body">
                        <p><strong>Model:</strong> ${droneType.model}</p>
                        <p><strong>Manufacturer:</strong> ${droneType.manufacturer}</p>
                        <p><strong>Country of Origin:</strong> ${droneType.country_of_origin}</p>
                        <p><strong>Range:</strong> ${droneType.range_km} km</p>
                        <p><strong>Endurance:</strong> ${droneType.endurance_minutes} minutes</p>
                        <p><strong>Max Altitude:</strong> ${droneType.max_altitude_m} meters</p>
                        <p><strong>Payload Type:</strong> ${droneType.payload_type}</p>
                        <p><strong>Intercept Difficulty:</strong> ${droneType.difficulty_intercept}/10</p>
                        <p><strong>Estimated Cost:</strong> \$${droneType.estimated_cost_usd?.toLocaleString() || 'N/A'}</p>
                        <p><strong>Notes:</strong> ${droneType.notes || 'N/A'}</p>
                    </div>
                </div>
                ` : ''}

                <div class="card">
                    <div class="card-header bg-primary">
                        <strong>Flight Path Visualization</strong>
                    </div>
                    <div class="card-body">
                        <div id="detailMapContainer" style="height: 400px; border-radius: 8px; margin-bottom: 10px;"></div>
                        <p class="text-muted small">
                            <i class="fas fa-circle" style="color: #dc3545;"></i> Sighting location at ${incident.sighting_date} ${incident.sighting_time}<br>
                            <i class="fas fa-square" style="color: #0d6efd;"></i> Restricted area location
                        </p>
                    </div>
                </div>
            `;

            document.getElementById('detailContent').innerHTML = html;

            // Initialize the detail map after a short delay to ensure DOM is ready
            setTimeout(() => {
                initDetailMap(incident, area);
            }, 100);

            // Show the modal using Bootstrap's method
            setTimeout(() => {
                try {
                    // Try using Bootstrap 5 API
                    if (typeof bootstrap !== 'undefined') {
                        const modalElement = document.getElementById('detailModal');
                        const modal = new bootstrap.Modal(modalElement);
                        modal.show();
                    } else {
                        // Fallback: use jQuery if available
                        console.warn('Bootstrap not available, trying fallback');
                        $('#detailModal').modal('show');
                    }
                } catch (error) {
                    console.error('Error showing modal:', error);
                }
            }, 150);
        };

        const autoDetectPatterns = async () => {
            try {
                const response = await fetch('/api/patterns/auto-detect', { method: 'POST' });
                const data = await response.json();
                alert(`Detected ${data.detected_patterns} new patterns`);
                fetchPatterns();
            } catch (error) {
                console.error('Error auto-detecting patterns:', error);
            }
        };

        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            const day = date.getDate();
            const month = date.getMonth() + 1;
            const year = date.getFullYear();
            return `${day}-${month}-${year}`;
        };

        const getThreatColor = (level) => {
            if (level >= 4) return 'danger';
            if (level >= 3) return 'warning';
            return 'info';
        };

        const initDetailMap = (incident, area) => {
            const mapElement = document.getElementById('detailMapContainer');
            if (!mapElement || !incident) return;

            // Remove old map if exists
            if (detailMap) {
                detailMap.remove();
                detailMap = null;
            }

            // Determine map center and zoom
            let centerLat = incident.latitude;
            let centerLon = incident.longitude;
            let zoom = 10;

            if (area) {
                // Center between incident and restricted area for better view
                centerLat = (incident.latitude + area.latitude) / 2;
                centerLon = (incident.longitude + area.longitude) / 2;
                zoom = 9;
            }

            // Create map
            detailMap = L.map('detailMapContainer').setView([centerLat, centerLon], zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(detailMap);

            // Add sighting location marker (red)
            L.circleMarker([incident.latitude, incident.longitude], {
                radius: 10,
                fillColor: '#dc3545',
                color: '#dc3545',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).bindPopup(`<strong>Sighting Location</strong><br/>${formatDate(incident.sighting_date)} ${incident.sighting_time}<br/>Altitude: ${incident.altitude_m}m<br/>Duration: ${incident.duration_minutes} min`)
                .addTo(detailMap)
                .openPopup();

            // Add restricted area marker (blue)
            if (area) {
                L.circleMarker([area.latitude, area.longitude], {
                    radius: 12,
                    fillColor: '#0d6efd',
                    color: '#0d6efd',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.7
                }).bindPopup(`<strong>${area.name}</strong><br/>Type: ${area.area_type}<br/>Threat Level: ${area.threat_level}/5`)
                    .addTo(detailMap);

                // Add protection radius circle
                L.circle([area.latitude, area.longitude], {
                    radius: (area.radius_km || 5) * 1000,
                    color: '#0d6efd',
                    weight: 2,
                    opacity: 0.4,
                    fillOpacity: 0.1,
                    dashArray: '5, 5'
                }).addTo(detailMap);

                // Draw line from sighting to restricted area
                L.polyline([
                    [incident.latitude, incident.longitude],
                    [area.latitude, area.longitude]
                ], {
                    color: '#ffc107',
                    weight: 2,
                    opacity: 0.6,
                    dashArray: '5, 5'
                }).addTo(detailMap);

                // Add distance annotation
                const distKm = Math.sqrt(
                    Math.pow(incident.latitude - area.latitude, 2) +
                    Math.pow(incident.longitude - area.longitude, 2)
                ) * 111; // Approximate km conversion

                const midLat = (incident.latitude + area.latitude) / 2;
                const midLon = (incident.longitude + area.longitude) / 2;

                L.circleMarker([midLat, midLon], {
                    radius: 0,
                    fillOpacity: 0
                }).bindPopup(`<strong>Distance: ${distKm.toFixed(1)} km</strong>`).addTo(detailMap);
            }

            // Add north arrow and scale
            L.control.scale().addTo(detailMap);
        };

        const initMap = () => {
            if (map) {
                map.remove();
            }

            const mapElement = document.getElementById('map');
            if (!mapElement) return;

            // Center on Europe
            map = L.map('map').setView([51.5, 10], 4);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19,
                style: { filter: 'invert(1)' }
            }).addTo(map);

            // Add restricted areas as markers
            restrictedAreas.value.forEach(area => {
                const color = area.threat_level >= 4 ? 'red' : area.threat_level >= 3 ? 'orange' : 'blue';
                L.circleMarker([area.latitude, area.longitude], {
                    radius: 8 + area.threat_level,
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.6,
                    dashArray: area.radius_km ? `${area.radius_km * 2}` : ''
                }).bindPopup(`<strong>${area.name}</strong><br/>Type: ${area.area_type}<br/>Threat: ${area.threat_level}/5`)
                    .addTo(map);

                // Add radius circle
                L.circle([area.latitude, area.longitude], {
                    radius: (area.radius_km || 5) * 1000,
                    color: color,
                    weight: 1,
                    opacity: 0.3,
                    fillOpacity: 0.1
                }).addTo(map);
            });
        };

        // Watch for view changes
        const watchView = (newView) => {
            if (newView === 'dashboard') {
                fetchStats();
            } else if (newView === 'incidents') {
                fetchIncidents();
            } else if (newView === 'drones') {
                fetchDroneTypes();
            } else if (newView === 'areas') {
                fetchRestrictedAreas();
            } else if (newView === 'patterns') {
                fetchPatterns();
            } else if (newView === 'interventions') {
                fetchInterventions();
            }
        };

        // View pattern details with intelligence
        const viewPattern = async (id) => {
            try {
                const response = await fetch(`/api/patterns/${id}`);
                const pattern = await response.json();
                if (!pattern) return;

                // Parse JSON fields
                let officialStatements = [];
                let expertAnalysis = [];
                let countermeasures = {};
                let relatedCampaigns = [];

                try {
                    if (pattern.official_statements_json) {
                        officialStatements = JSON.parse(pattern.official_statements_json);
                    }
                    if (pattern.expert_analysis_json) {
                        expertAnalysis = JSON.parse(pattern.expert_analysis_json);
                    }
                    if (pattern.countermeasures_json) {
                        countermeasures = JSON.parse(pattern.countermeasures_json);
                    }
                    if (pattern.related_campaigns_json) {
                        relatedCampaigns = JSON.parse(pattern.related_campaigns_json);
                    }
                } catch (e) {
                    console.error('Error parsing JSON fields:', e);
                }

                // Build official statements HTML
                let statementsHtml = '';
                if (officialStatements.length > 0) {
                    statementsHtml = officialStatements.map(stmt => `
                        <div class="alert alert-warning mb-2">
                            <strong><i class="fas fa-quote-left"></i> ${stmt.source}</strong>
                            <small class="text-muted ml-2">(${stmt.date})</small>
                            <p class="mb-1 mt-2">"${stmt.statement}"</p>
                            <div class="progress" style="height: 5px;">
                                <div class="progress-bar bg-success" role="progressbar"
                                     style="width: ${stmt.credibility * 10}%"></div>
                            </div>
                            <small class="text-muted">Credibility: ${stmt.credibility}/10</small>
                        </div>
                    `).join('');
                }

                // Build expert analysis HTML
                let analysisHtml = '';
                if (expertAnalysis.length > 0) {
                    analysisHtml = expertAnalysis.map(expert => `
                        <div class="alert alert-info mb-2">
                            <strong><i class="fas fa-user-tie"></i> ${expert.expert}</strong>
                            <p class="mb-1 mt-2">${expert.assessment}</p>
                            <small class="text-muted">Confidence: ${(expert.confidence * 100).toFixed(0)}%</small>
                        </div>
                    `).join('');
                }

                // Build countermeasures HTML
                let countermeasuresHtml = '';
                if (Object.keys(countermeasures).length > 0) {
                    countermeasuresHtml = Object.entries(countermeasures).map(([key, value]) => `
                        <tr>
                            <td><strong>${key.replace(/_/g, ' ')}</strong></td>
                            <td>${value}</td>
                        </tr>
                    `).join('');
                }

                // Build related campaigns HTML
                let campaignsHtml = '';
                if (relatedCampaigns.length > 0) {
                    campaignsHtml = relatedCampaigns.map(campaign => `
                        <li><i class="fas fa-link"></i> ${campaign}</li>
                    `).join('');
                }

                const content = `
                    <div class="pattern-detail">
                        <h4>${pattern.name}</h4>
                        <p class="text-muted">
                            <span class="badge badge-secondary">${pattern.pattern_type}</span>
                            ${pattern.incident_count} incidents
                        </p>

                        ${pattern.threat_actor ? `
                        <div class="alert alert-danger">
                            <h5><i class="fas fa-user-secret"></i> Threat Actor Attribution</h5>
                            <p><strong>${pattern.threat_actor}</strong></p>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-danger" role="progressbar"
                                     style="width: ${(pattern.threat_actor_confidence * 100).toFixed(0)}%">
                                    ${(pattern.threat_actor_confidence * 100).toFixed(0)}% Confidence
                                </div>
                            </div>
                            ${pattern.threat_level_justification ? `
                                <small><strong>Justification:</strong> ${pattern.threat_level_justification}</small>
                            ` : ''}
                        </div>
                        ` : ''}

                        ${pattern.geopolitical_context ? `
                        <div class="alert alert-secondary">
                            <h5><i class="fas fa-globe"></i> Geopolitical Context</h5>
                            <p style="white-space: pre-wrap;">${pattern.geopolitical_context}</p>
                        </div>
                        ` : ''}

                        ${pattern.strategic_intent ? `
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-chess"></i> Strategic Intent</h5>
                            <p>${pattern.strategic_intent}</p>
                        </div>
                        ` : ''}

                        ${pattern.modus_operandi ? `
                        <div class="alert alert-info">
                            <h5><i class="fas fa-cogs"></i> Modus Operandi</h5>
                            <p>${pattern.modus_operandi}</p>
                        </div>
                        ` : ''}

                        ${statementsHtml ? `
                        <h5 class="mt-4"><i class="fas fa-landmark"></i> Official Statements</h5>
                        ${statementsHtml}
                        ` : ''}

                        ${analysisHtml ? `
                        <h5 class="mt-4"><i class="fas fa-brain"></i> Expert Analysis</h5>
                        ${analysisHtml}
                        ` : ''}

                        ${countermeasuresHtml ? `
                        <h5 class="mt-4"><i class="fas fa-shield-alt"></i> Countermeasure Effectiveness</h5>
                        <table class="table table-sm">
                            <tbody>
                                ${countermeasuresHtml}
                            </tbody>
                        </table>
                        ` : ''}

                        ${campaignsHtml ? `
                        <h5 class="mt-4"><i class="fas fa-project-diagram"></i> Related Campaigns</h5>
                        <ul>
                            ${campaignsHtml}
                        </ul>
                        ` : ''}
                    </div>
                `;

                // Show in modal
                const modal = new bootstrap.Modal(document.getElementById('detailModal'));
                document.getElementById('detailModalLabel').textContent = 'Intelligence Pattern Details';
                document.getElementById('detailModalBody').innerHTML = content;
                modal.show();

            } catch (error) {
                console.error('Error fetching pattern details:', error);
            }
        };

        // Lifecycle
        onMounted(() => {
            fetchStats();
        });

        return {
            currentView,
            loading,
            stats,
            incidents,
            droneTypes,
            restrictedAreas,
            patterns,
            interventionEffectiveness,
            interventionStats,
            selectedIncident,
            filteredIncidents,
            sortColumn,
            sortDirection,
            fetchStats,
            fetchIncidents,
            fetchDroneTypes,
            fetchRestrictedAreas,
            fetchPatterns,
            fetchInterventions,
            viewIncident,
            viewPattern,
            viewSourceDetail,
            autoDetectPatterns,
            formatDate,
            getThreatColor,
            getLocationName,
            getCountryFromArea,
            getSourceName,
            initDetailMap,
            sortBy,
            getSortClass,
            watch: () => {
                // Manual watch implementation
                const watchCurrentView = setInterval(() => {
                    // Implement view-based data loading
                }, 500);
                return () => clearInterval(watchCurrentView);
            }
        };
    },
    watch: {
        currentView(newView) {
            if (newView === 'dashboard') {
                this.fetchStats();
                this.fetchIncidents();
            } else if (newView === 'drones') {
                this.fetchDroneTypes();
            } else if (newView === 'areas') {
                this.fetchRestrictedAreas();
            } else if (newView === 'patterns') {
                this.fetchPatterns();
            } else if (newView === 'interventions') {
                this.fetchInterventions();
            }
        }
    }
});

app.mount('#app');
