/**
 * Health Trends Visualization
 * Renders interactive sparkline charts and trend indicators for historical data
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Health score color thresholds
    const HEALTH_COLORS = {
        healthy: '#10b981',   // Green (80+)
        warning: '#f59e0b',   // Yellow (60-79)
        critical: '#ef4444',  // Red (<60)
        default: '#6366f1'     // Indigo (default)
    };

    // Find all sparkline containers
    const sparklines = document.querySelectorAll('.sparkline');
    const trendIndicators = document.querySelectorAll('.trend-indicator');

    // Initialize sparklines
    sparklines.forEach(function(container) {
        renderSparkline(container, HEALTH_COLORS);
    });

    // Initialize trend indicators
    trendIndicators.forEach(function(container) {
        renderTrendIndicator(container);
    });

    /**
     * Render a sparkline chart
     */
    function renderSparkline(container, colors) {
        const valuesAttr = container.getAttribute('data-values');
        if (!valuesAttr) return;

        // Parse values (comma-separated string)
        const values = valuesAttr.split(',')
            .map(v => parseFloat(v.trim()))
            .filter(v => !isNaN(v));

        if (values.length === 0) return;

        // Get optional parameters
        const isCritical = container.classList.contains('critical');
        const showLine = container.getAttribute('data-type') === 'line';
        const showLabels = container.getAttribute('data-labels');
        const color = isCritical ? colors.critical : colors.default;

        // Calculate min and max for normalization
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;

        // Clear container
        container.innerHTML = '';

        if (showLine) {
            renderLineChart(container, values, min, range, colors, color);
        } else {
            renderBarChart(container, values, min, range, colors, isCritical);
        }
    }

    /**
     * Render bar-style sparkline
     */
    function renderBarChart(container, values, min, range, colors, isCritical) {
        const barWidth = 100 / values.length;

        values.forEach(function(value, index) {
            const bar = document.createElement('div');
            bar.className = 'sparkline-bar';

            // Calculate height percentage (minimum 5% for visibility)
            const normalizedValue = (value - min) / range;
            const heightPercent = Math.max(5, normalizedValue * 100);

            // Determine color based on health score (if not critical variant)
            let barColor;
            if (isCritical) {
                barColor = colors.critical;
            } else {
                if (value >= 80) barColor = colors.healthy;
                else if (value >= 60) barColor = colors.warning;
                else barColor = colors.critical;
            }

            bar.style.height = heightPercent + '%';
            bar.style.width = barWidth + '%';
            bar.style.backgroundColor = barColor;
            bar.title = `Value: ${value.toFixed(1)}`;
            bar.setAttribute('data-value', value);
            bar.setAttribute('data-index', index);

            // Add hover effect with tooltip
            bar.addEventListener('mouseenter', function(e) {
                showTooltip(e, value, colors);
            });

            bar.addEventListener('mouseleave', function() {
                hideTooltip();
            });

            container.appendChild(bar);
        });
    }

    /**
     * Render line-style sparkline (SVG)
     */
    function renderLineChart(container, values, min, range, colors, color) {
        const width = container.offsetWidth || 200;
        const height = container.offsetHeight || 60;
        const padding = 2;

        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.setAttribute('preserveAspectRatio', 'none');

        // Generate path data
        const points = values.map(function(value, index) {
            const x = (index / (values.length - 1)) * (width - padding * 2) + padding;
            const y = height - ((value - min) / range) * (height - padding * 2) - padding;
            return { x, y, value };
        });

        // Create gradient
        const gradientId = 'sparkline-gradient-' + Math.random().toString(36).substr(2, 9);
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', gradientId);
        gradient.setAttribute('x1', '0%');
        gradient.setAttribute('y1', '0%');
        gradient.setAttribute('x2', '0%');
        gradient.setAttribute('y2', '100%');

        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('stop-color', color);
        stop1.setAttribute('stop-opacity', '0.3');

        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '100%');
        stop2.setAttribute('stop-color', color);
        stop2.setAttribute('stop-opacity', '0');

        gradient.appendChild(stop1);
        gradient.appendChild(stop2);

        // Create area fill
        const areaPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const areaD = `M ${points[0].x} ${height} ` +
                     points.map(p => `L ${p.x} ${p.y}`).join(' ') +
                     ` L ${points[points.length - 1].x} ${height} Z`;
        areaPath.setAttribute('d', areaD);
        areaPath.setAttribute('fill', `url(#${gradientId})`);

        // Create line path
        const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const lineD = `M ${points[0].x} ${points[0].y} ` +
                      points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ');
        linePath.setAttribute('d', lineD);
        linePath.setAttribute('fill', 'none');
        linePath.setAttribute('stroke', color);
        linePath.setAttribute('stroke-width', '2');
        linePath.setAttribute('stroke-linecap', 'round');
        linePath.setAttribute('stroke-linejoin', 'round');

        // Create data points
        points.forEach(function(point, index) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', point.x);
            circle.setAttribute('cy', point.y);
            circle.setAttribute('r', index === points.length - 1 ? 4 : 3);
            circle.setAttribute('fill', color);
            circle.setAttribute('stroke', '#fff');
            circle.setAttribute('stroke-width', '2');
            circle.style.cursor = 'pointer';
            circle.title = `Value: ${point.value.toFixed(1)}`;

            circle.addEventListener('mouseenter', function(e) {
                showTooltip(e, point.value, colors);
            });

            circle.addEventListener('mouseleave', function() {
                hideTooltip();
            });

            svg.appendChild(circle);
        });

        svg.appendChild(areaPath);
        svg.appendChild(linePath);
        container.appendChild(svg);
    }

    /**
     * Render trend indicator (up/down/stable arrow)
     */
    function renderTrendIndicator(container) {
        const currentAttr = container.getAttribute('data-current');
        const previousAttr = container.getAttribute('data-previous');

        if (!currentAttr || !previousAttr) return;

        const current = parseFloat(currentAttr);
        const previous = parseFloat(previousAttr);

        if (isNaN(current) || isNaN(previous)) return;

        const diff = current - previous;
        const percentDiff = previous !== 0 ? (diff / previous) * 100 : 0;

        let trend, icon, color;

        if (diff > 2) {
            trend = 'up';
            icon = '↑';
            color = '#10b981';
        } else if (diff < -2) {
            trend = 'down';
            icon = '↓';
            color = '#ef4444';
        } else {
            trend = 'stable';
            icon = '→';
            color = '#f59e0b';
        }

        container.className = `trend-indicator trend-${trend}`;
        container.innerHTML = `
            <span class="trend-icon" style="color: ${color}">${icon}</span>
            <span class="trend-value">${current.toFixed(1)}</span>
            <span class="trend-diff" style="color: ${color}">
                ${diff > 0 ? '+' : ''}${diff.toFixed(1)} (${percentDiff > 0 ? '+' : ''}${percentDiff.toFixed(1)}%)
            </span>
        `;
    }

    /**
     * Show tooltip on hover
     */
    function showTooltip(event, value, colors) {
        hideTooltip(); // Remove existing tooltip

        let tooltipColor;
        if (value >= 80) tooltipColor = colors.healthy;
        else if (value >= 60) tooltipColor = colors.warning;
        else tooltipColor = colors.critical;

        const tooltip = document.createElement('div');
        tooltip.className = 'sparkline-tooltip';
        tooltip.innerHTML = `
            <span class="tooltip-value" style="color: ${tooltipColor}">${value.toFixed(1)}</span>
        `;

        // Position tooltip
        const rect = event.target.getBoundingClientRect();
        tooltip.style.position = 'fixed';
        tooltip.style.left = rect.left + rect.width / 2 + 'px';
        tooltip.style.top = (rect.top - 30) + 'px';
        tooltip.style.transform = 'translateX(-50%)';
        tooltip.style.zIndex = '1000';

        document.body.appendChild(tooltip);
        event.target._tooltip = tooltip;
    }

    /**
     * Hide tooltip
     */
    function hideTooltip() {
        const existing = document.querySelector('.sparkline-tooltip');
        if (existing) {
            existing.remove();
        }
    }

    /**
     * Auto-resize sparklines on window resize
     */
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            sparklines.forEach(function(container) {
                container.innerHTML = '';
                renderSparkline(container, HEALTH_COLORS);
            });
        }, 250);
    });
});
