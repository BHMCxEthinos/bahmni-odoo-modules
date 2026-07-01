// Helpdesk Dashboard JavaScript
(function() {
    'use strict';

    // Chart instances
    var ticketTrendChart = null;
    var stateDistributionChart = null;
    var priorityDistributionChart = null;
    var slaStatusChart = null;
    
    // Current filters
    var currentFilters = {
        date_from: null,
        date_to: null,
        team_id: null,
        state: null
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
    
    // Load Chart.js library
    function loadChartLibrary() {
        return new Promise(function(resolve, reject) {
            if (window.Chart) {
                resolve(window.Chart);
                return;
            }
            
            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
            script.onload = function() {
                resolve(window.Chart);
            };
            script.onerror = function() {
                reject(new Error('Failed to load Chart.js library'));
            };
            document.head.appendChild(script);
        });
    }
    
    var HelpdeskDashboard = {
        Chart: null,
        
        init: function() {
            var self = this;
            
            // Load Chart.js and initialize
            loadChartLibrary().then(function(Chart) {
                self.Chart = Chart;
                self.loadTeams();
                self.loadKPIs();
                self.setupEventListeners();
            }).catch(function(error) {
                console.error('Failed to initialize dashboard:', error);
                $('#helpdesk-loading-overlay').hide();
            });
        },
        
        setupEventListeners: function() {
            var self = this;
            
            $('#btn-apply-filters').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.applyFilters();
                return false;
            });
            
            $('#btn-reset-filters').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.resetFilters();
                return false;
            });
            
            $('#btn-refresh-dashboard').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.loadKPIs();
                self.loadCharts();
                return false;
            });
        },
        
        loadTeams: function() {
            var self = this;
            rpcQuery('/helpdesk/dashboard/teams', {}).then(function(result) {
                if (result.success && result.data) {
                    // Populate team dropdown (same as team dashboard)
                    var select = $('#filter-team');
                    select.empty();
                    select.append('<option value="">All Teams</option>');
                    result.data.forEach(function(team) {
                        select.append('<option value="' + team.id + '">' + team.name + '</option>');
                    });
                }
            }).catch(function(error) {
                console.error('Error loading teams:', error);
            });
        },
        
        loadKPIs: function() {
            var self = this;
            $('#helpdesk-loading-overlay').show();
            
            var params = {
                date_from: currentFilters.date_from || null,
                date_to: currentFilters.date_to || null,
                team_id: currentFilters.team_id || null,
                state: currentFilters.state || null
            };
            
            rpcQuery('/helpdesk/dashboard/kpis', params).then(function(result) {
                if (result.success && result.kpis) {
                    self.updateKPIs(result.kpis);
                    self.loadCharts();
                }
            }).catch(function(error) {
                console.error('Error loading KPIs:', error);
            }).finally(function() {
                $('#helpdesk-loading-overlay').hide();
            });
        },
        
        updateKPIs: function(kpis) {
            $('#total-tickets').text(kpis.total_tickets || 0);
            $('#my-tickets').text(kpis.my_tickets || 0);
            $('#unassigned').text(kpis.unassigned || 0);
            $('#sla-risk').text(kpis.sla_at_risk || 0);
            $('#today-tickets').text(kpis.today_tickets || 0);
            $('#overdue-count').text(kpis.overdue_count || 0);
            $('#resolved-today').text(kpis.resolved_today || 0);
            $('#total-reminders').text(kpis.total_reminders || 0);
            $('#pending-reminders').text(kpis.pending_reminders || 0);
            $('#sent-reminders').text(kpis.sent_reminders || 0);
            $('#upcoming-reminders').text(kpis.upcoming_reminders || 0);
        },
        
        loadCharts: function() {
            var self = this;
            
            // Load ticket trend
            self.loadTicketTrend();
            
            // Load state distribution
            self.loadStateDistribution();
            
            // Load priority distribution
            self.loadPriorityDistribution();
            
            // Load SLA status
            self.loadSLAStatus();
        },
        
        loadTicketTrend: function() {
            var self = this;
            var params = {
                months: 12,
                team_id: currentFilters.team_id || null,
                state: currentFilters.state || null
            };
            
            rpcQuery('/helpdesk/dashboard/ticket-trend', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderTicketTrendChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading ticket trend:', error);
            });
        },
        
        loadStateDistribution: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/state-distribution', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderStateDistributionChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading state distribution:', error);
            });
        },
        
        loadPriorityDistribution: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/priority-distribution', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderPriorityDistributionChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading priority distribution:', error);
            });
        },
        
        loadSLAStatus: function() {
            var self = this;
            var params = {
                team_id: currentFilters.team_id || null
            };
            
            rpcQuery('/helpdesk/dashboard/sla-status', params).then(function(result) {
                if (result.success && result.data) {
                    self.renderSLAStatusChart(result.data);
                }
            }).catch(function(error) {
                console.error('Error loading SLA status:', error);
            });
        },
        
        renderTicketTrendChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-ticket-trend');
            if (!ctx) return;
            
            if (ticketTrendChart) {
                ticketTrendChart.destroy();
            }
            
            ticketTrendChart = new self.Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Tickets Created',
                        data: data.values || [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        },
        
        renderStateDistributionChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-state-distribution');
            if (!ctx) return;
            
            if (stateDistributionChart) {
                stateDistributionChart.destroy();
            }
            
            stateDistributionChart = new self.Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)',
                            'rgba(255, 159, 64, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        },
        
        renderPriorityDistributionChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-priority-distribution');
            if (!ctx) return;
            
            if (priorityDistributionChart) {
                priorityDistributionChart.destroy();
            }
            
            priorityDistributionChart = new self.Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Tickets by Priority',
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',   // Low - Green
                            'rgba(255, 193, 7, 0.8)',   // Medium - Yellow
                            'rgba(253, 126, 20, 0.8)',   // High - Orange
                            'rgba(220, 53, 69, 0.8)'     // Urgent - Red
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        },
        
        renderSLAStatusChart: function(data) {
            var self = this;
            var ctx = document.getElementById('chart-sla-status');
            if (!ctx) return;
            
            if (slaStatusChart) {
                slaStatusChart.destroy();
            }
            
            slaStatusChart = new self.Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',   // Met - Green
                            'rgba(255, 193, 7, 0.8)',   // At Risk - Yellow
                            'rgba(220, 53, 69, 0.8)',   // Breached - Red
                            'rgba(108, 117, 125, 0.8)'   // No SLA - Gray
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        },
        
        applyFilters: function() {
            var self = this;
            
            // Read filter values from HTML input/select fields (same as team dashboard)
            currentFilters.date_from = $('#filter-date-from').val() || null;
            currentFilters.date_to = $('#filter-date-to').val() || null;
            currentFilters.team_id = $('#filter-team').val() || null;
            currentFilters.state = $('#filter-state').val() || null;
            
            // Reload KPIs and charts with new filters (no page reload)
            self.loadKPIs();
        },
        
        resetFilters: function() {
            var self = this;
            
            // Clear HTML input/select fields (same as team dashboard)
            $('#filter-date-from').val('');
            $('#filter-date-to').val('');
            $('#filter-team').val('');
            $('#filter-state').val('');
            
            // Reset filter object
            currentFilters = {
                date_from: null,
                date_to: null,
                team_id: null,
                state: null
            };
            
            // Reload KPIs with cleared filters (no page reload)
            self.loadKPIs();
        }
    };
    
    // Initialize dashboard when DOM is ready
    // Use multiple initialization methods to ensure it works in Odoo
    $(document).ready(function() {
        // Small delay to ensure Odoo form view is fully loaded
        setTimeout(function() {
            if (typeof HelpdeskDashboard !== 'undefined') {
                HelpdeskDashboard.init();
            }
        }, 1000);
    });
    
    // Also try to initialize when page is fully loaded
    if (document.readyState === 'complete') {
        setTimeout(function() {
            if (typeof HelpdeskDashboard !== 'undefined') {
                HelpdeskDashboard.init();
            }
        }, 500);
    } else {
        window.addEventListener('load', function() {
            setTimeout(function() {
                if (typeof HelpdeskDashboard !== 'undefined') {
                    HelpdeskDashboard.init();
                }
            }, 500);
        });
    }
    
})();
