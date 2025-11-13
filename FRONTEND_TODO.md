# Frontend Views - Implementatie Plan

**Datum:** 13 November 2025
**Status:** Planning

---

## Overzicht

We hebben 4 nieuwe frontend views nodig om de backend intelligence te visualiseren:

1. ✅ **Blockchain Intel View** - Transaction graphs en wallet profiling
2. ✅ **Forum Monitoring View** - Suspicious accounts tracking
3. ⏳ **Enhanced Patterns View** - Operational classification badges
4. ⏳ **Orlan Analysis Map** - Launch range visualization

---

## 1. Blockchain Intel View

### Features:
- **Wallet Table**: 7 wallets sorted by risk score
- **Transaction Graph**: vis.js network visualization (Handler → Mixer → Operative)
- **Exchange Connections**: Law enforcement contact info
- **LEA Report Button**: Generate law enforcement report per incident

### API Endpoints:
- `GET /api/blockchain/wallets`
- `GET /api/blockchain/transaction-graph`
- `GET /api/blockchain/exchange-connections`
- `GET /api/blockchain/law-enforcement-report/{incident_id}`

### UI Components:
```html
<div class="blockchain-view">
  <div class="row">
    <div class="col-md-6">
      <div class="card">
        <h5>Wallet Profiles (Risk Scores)</h5>
        <table>...</table>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card">
        <h5>Transaction Graph</h5>
        <div id="transaction-graph"></div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-12">
      <div class="card">
        <h5>Exchange Connections (Law Enforcement)</h5>
        <table>
          <tr>
            <td>Bitonic NL</td>
            <td>FIOD: +31 20 574 3774</td>
            <td>€2,000 cash-out</td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</div>
```

---

## 2. Forum Monitoring View

### Features:
- **Monitored Forums Table**: 6 forums with threat levels
- **Suspicious Accounts**: 2 tracked accounts with red flags
- **Red Flag Library**: 15 behavioral patterns
- **Detection Summary**: Stats dashboard

### API Endpoints:
- `GET /api/forums/monitored-forums`
- `GET /api/forums/suspicious-accounts`
- `GET /api/forums/red-flags`
- `GET /api/forums/detection-summary`

### UI Components:
```html
<div class="forums-view">
  <div class="row mb-3">
    <div class="col-md-12">
      <div class="alert alert-info">
        <i class="fas fa-info-circle"></i>
        <strong>Counter-Intelligence:</strong> Detecting GRU-recruited spotters infiltrating aviation forums
      </div>
    </div>
  </div>

  <div class="row">
    <div class="col-md-8">
      <div class="card">
        <h5>Suspicious Accounts (0.75+ Risk)</h5>
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Forum</th>
              <th>Location</th>
              <th>Risk Score</th>
              <th>Red Flags</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr class="table-danger">
              <td>AvGeek_NL_2025</td>
              <td>Airliners.net</td>
              <td>Amsterdam</td>
              <td>0.82</td>
              <td>5 flags</td>
              <td><span class="badge bg-danger">High Priority</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-md-4">
      <div class="card">
        <h5>Detection Summary</h5>
        <ul class="list-unstyled">
          <li>🎯 Total Accounts: 2</li>
          <li>⚠️ High Priority: 1</li>
          <li>🚨 LEA Referral: 1</li>
          <li>👁️ Forums Monitored: 6</li>
        </ul>
      </div>
    </div>
  </div>
</div>
```

---

## 3. Enhanced Patterns View (TODO)

### Features:
- **Classification Badges**: Visual indicators (🎖️ STATE_ACTOR, 💰 RECRUITED_LOCAL)
- **Counter-Measures Cards**: Recommended C-UAS systems per incident
- **Strategic Dashboard**: Cost comparison, effectiveness ratings

### Mockup:
```
Incident #10: Brunsbüttel Nuclear
[🎖️ STATE_ACTOR] [Risk: CRITICAL]

Strategic Assessment:
Russian military-grade reconnaissance drone (Orlan-10)...

Counter-Measures Recommended:
┌─────────────────────────────────────┐
│ 🔴 CRITICAL - AUDS System          │
│ Range: 10km | Cost: €850K           │
│ Effectiveness: 85%                   │
│ Deploy: North perimeter             │
└─────────────────────────────────────┘
```

---

## 4. Orlan Analysis Map (TODO)

### Features:
- **Leaflet Map Integration**: Existing map view
- **Launch Range Circles**: 120km radius from Orlan-10 sighting
- **Possible Launch Sites**: Baltic Sea, Poland border, Belarus
- **AIS Integration Note**: "Correlate with vessel tracking"

### Implementation:
```javascript
// In existing map view (areas), add layer toggle
const orlanIncidents = ref([]);

async function fetchOrlanAnalysis() {
  const response = await fetch('/api/patterns/orlan-analysis');
  const data = await response.json();
  orlanIncidents.value = data.orlan_incidents;

  // Draw circles on map
  orlanIncidents.value.forEach(incident => {
    if (incident.possible_launch_zone) {
      L.circle([
        incident.possible_launch_zone.center_lat,
        incident.possible_launch_zone.center_lon
      ], {
        radius: incident.possible_launch_zone.radius_km * 1000,
        color: 'red',
        fillColor: '#f03',
        fillOpacity: 0.2
      }).addTo(map).bindPopup(`
        <strong>Orlan-10 Launch Range</strong><br>
        Radius: ${incident.possible_launch_zone.radius_km}km<br>
        ${incident.possible_launch_zone.analysis}
      `);
    }
  });
}
```

---

## Implementatie Volgorde

### Fase 1: Nieuwe Sidebar Items (5 min)
- [ ] Add "Blockchain Intel" sidebar item
- [ ] Add "Forum Monitoring" sidebar item

### Fase 2: Blockchain View (20 min)
- [ ] Create basic wallet table
- [ ] Add transaction graph (vis.js)
- [ ] Add exchange connections table
- [ ] Add LEA report button

### Fase 3: Forum View (15 min)
- [ ] Create forums table
- [ ] Add suspicious accounts table
- [ ] Add detection summary cards
- [ ] Add red flags modal

### Fase 4: Enhanced Patterns (10 min)
- [ ] Add classification badges to existing patterns view
- [ ] Add counter-measures section to incident details
- [ ] Add strategic dashboard stats

### Fase 5: Orlan Map (10 min)
- [ ] Add layer toggle to existing map
- [ ] Draw 120km circles for Orlan incidents
- [ ] Add launch analysis popup

**Total Estimated Time:** ~60 minutes

---

## Dependencies

### JavaScript Libraries (Already Loaded):
- ✅ Vue.js 3
- ✅ Bootstrap 5
- ✅ Leaflet
- ✅ vis.js (for network graphs)
- ✅ Font Awesome

### New Libraries Needed:
- None! All dependencies already in place.

---

## Notes

- Keep views **simple and focused**
- Use existing Bootstrap components
- Reuse existing CSS/styling
- Mobile-responsive by default
- **Test thoroughly** before committing

---

**Next Step:** Begin Fase 1 - Add sidebar items and basic structure for both views.
