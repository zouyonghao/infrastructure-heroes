/**
 * Health Trends Visualization
 * Renders sparkline charts for historical data
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Find all sparkline containers
    const sparklines = document.querySelectorAll('.sparkline');
    
    sparklines.forEach(function(container) {
        const valuesAttr = container.getAttribute('data-values');
        if (!valuesAttr) return;
        
        // Parse values (comma-separated string)
        const values = valuesAttr.split(',')
            .map(v => parseFloat(v.trim()))
            .filter(v => !isNaN(v));
        
        if (values.length === 0) return;
        
        // Calculate min and max for normalization
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1; // Avoid division by zero
        
        // Clear container
        container.innerHTML = '';
        
        // Create bars
        values.forEach(function(value, index) {
            const bar = document.createElement('div');
            bar.className = 'sparkline-bar';
            
            // Calculate height percentage (minimum 10% for visibility)
            const normalizedValue = (value - min) / range;
            const heightPercent = Math.max(10, normalizedValue * 100);
            
            bar.style.height = heightPercent + '%';
            bar.title = `Value: ${value.toFixed(1)}`;
            
            // Add data attribute for potential future use
            bar.setAttribute('data-value', value);
            bar.setAttribute('data-index', index);
            
            container.appendChild(bar);
        });
    });
});
