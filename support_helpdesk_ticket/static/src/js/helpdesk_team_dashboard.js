// Helpdesk Team Dashboard JavaScript
(function() {
    'use strict';
    
    // Current filters
    var currentFilters = {
        date_from: null,
        date_to: null,
        team_id: null
    };
    
    // RPC helper
    function rpcQuery(route, params) {
        return new Promise(function(resolve, reject) {
            var csrfToken = $('meta[name="csrf-token"]').attr('content') || '';
            
            $.ajax({
                url: route,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: params || {},
                    id: Math.floor(Math.random() * 1000000)
                }),
                dataType: 'json',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                success: function(result) {
                    if (result.result) {
                        resolve(result.result);
                    } else if (result.error) {
                        reject(new Error(result.error.message || 'RPC error'));
                    } else {
                        resolve(result);
                    }
                },
                error: function(xhr, status, error) {
                    var errorMsg = 'Request failed';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error.message || errorMsg;
                    }
                    reject(new Error(errorMsg));
                }
            });
        });
    }
    
    var HelpdeskTeamDashboard = {
        init: function() {
            var self = this;
            
            self.loadTeams();
            self.loadKPIs();
            self.setupEventListeners();
        },
        
        setupEventListeners: function() {
            var self = this;
            
            $('#btn-apply-team-filters').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.applyFilters();
                return false;
            });
            
            $('#btn-reset-team-filters').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.resetFilters();
                return false;
            });
            
            $('#btn-refresh-team-dashboard').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.loadKPIs();
                return false;
            });
        },
        
        loadTeams: function() {
            var self = this;
            
            rpcQuery('/helpdesk/dashboard/teams', {}).then(function(result) {
                if (result.success && result.data) {
                    var select = $('#team-filter-team');
                    select.empty();
                    select.append('<option value="">All Teams</option>');
                    
                    result.data.forEach(function(team) {
                        select.append('<option value="' + team.id + '">' + team.name + '</option>');
                    });
                }
            }).catch(function(error) {
                console.error('Failed to load teams:', error);
            });
        },
        
        loadKPIs: function() {
            var self = this;
            
            self.showLoadingOverlay();
            
            var params = {
                date_from: currentFilters.date_from || null,
                date_to: currentFilters.date_to || null,
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/team/dashboard/kpis', params).then(function(result) {
                if (result.success && result.kpis) {
                    self.updateKPIs(result.kpis);
                    self.updateTeamPerformanceTable(result.kpis.team_performance || []);
                } else {
                    console.error('Failed to load KPIs:', result.error);
                }
                self.hideLoadingOverlay();
            }).catch(function(error) {
                console.error('Failed to load KPIs:', error);
                self.hideLoadingOverlay();
            });
        },
        
        updateKPIs: function(kpis) {
            $('#total-teams').text(kpis.total_teams || 0);
            $('#active-teams').text(kpis.active_teams || 0);
            $('#total-team-tickets').text(kpis.total_team_tickets || 0);
            $('#open-team-tickets').text(kpis.open_team_tickets || 0);
            $('#today-team-tickets').text(kpis.today_team_tickets || 0);
            $('#team-sla-at-risk').text(kpis.team_sla_at_risk || 0);
        },
        
        updateTeamPerformanceTable: function(teamPerformance) {
            var tbody = $('#team-performance-tbody');
            tbody.empty();
            
            if (teamPerformance.length === 0) {
                tbody.append('<tr><td colspan="6" class="text-center">No team data available</td></tr>');
                return;
            }
            
            teamPerformance.forEach(function(team) {
                var row = '<tr>' +
                    '<td><strong>' + (team.team_name || 'N/A') + '</strong></td>' +
                    '<td>' + (team.team_leader || 'N/A') + '</td>' +
                    '<td>' + (team.member_count || 0) + '</td>' +
                    '<td>' + (team.total_tickets || 0) + '</td>' +
                    '<td><span class="badge badge-warning">' + (team.open_tickets || 0) + '</span></td>' +
                    '<td><span class="badge badge-success">' + (team.resolved_tickets || 0) + '</span></td>' +
                    '</tr>';
                tbody.append(row);
            });
        },
        
        applyFilters: function() {
            currentFilters.date_from = $('#team-filter-date-from').val() || null;
            currentFilters.date_to = $('#team-filter-date-to').val() || null;
            currentFilters.team_id = $('#team-filter-team').val() || null;
            
            this.loadKPIs();
        },
        
        resetFilters: function() {
            $('#team-filter-date-from').val('');
            $('#team-filter-date-to').val('');
            $('#team-filter-team').val('');
            
            currentFilters = {
                date_from: null,
                date_to: null,
                team_id: null
            };
            
            this.loadKPIs();
        },
        
        showLoadingOverlay: function() {
            $('#team-loading-overlay').show();
        },
        
        hideLoadingOverlay: function() {
            $('#team-loading-overlay').hide();
        }
    };
    
    // Initialize dashboard when DOM is ready
    $(document).ready(function() {
        setTimeout(function() {
            HelpdeskTeamDashboard.init();
        }, 500);
    });
    
})();
