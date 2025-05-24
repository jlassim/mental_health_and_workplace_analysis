document.addEventListener('DOMContentLoaded', () => {
    const countryFilter = document.getElementById('country-filter');
    const genderFilter = document.getElementById('gender-filter');
    const ageRange = document.getElementById('age-range');
    const ageValue = document.getElementById('age-value');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const resetFiltersBtn = document.getElementById('reset-filters');

    ageRange.addEventListener('input', () => {
        ageValue.textContent = `Up to ${ageRange.value}`;
    });

    const genders = ['All', 'Male', 'Female', 'Other'];
    genders.forEach(g => {
        const option = document.createElement('option');
        option.value = g.toLowerCase();
        option.textContent = g;
        genderFilter.appendChild(option);
    });

    function initPage() {
        d3.csv("final_data.csv").then(data => {
            window.surveyData = data.map(row => {
                // Clean and normalize data
                row.age = row.age ? +row.age : null;
                
                if (row.gender) {
                    const g = row.gender.toLowerCase();
                    if (g.includes('female')) row.gender = 'female';
                    else if (g.includes('male')) row.gender = 'male';
                    else row.gender = 'other';
                } else {
                    row.gender = 'other';
                }
                
                // Clean text fields
                row.mental_health_consequence = row.mental_health_consequence ? row.mental_health_consequence.trim() : 'Unknown';
                row.phys_health_consequence = row.phys_health_consequence ? row.phys_health_consequence.trim() : 'Unknown';
                row.mental_health_interview = row.mental_health_interview ? row.mental_health_interview.trim() : 'Unknown';
                row.phys_health_interview = row.phys_health_interview ? row.phys_health_interview.trim() : 'Unknown';
                row.coworkers = row.coworkers ? row.coworkers.trim() : 'Unknown';
                row.mental_vs_physical = row.mental_vs_physical ? row.mental_vs_physical.trim() : 'Unknown';
                
                return row;
            });

            if (typeof window.commonPopulateCountryOptions === 'function') {
                window.commonPopulateCountryOptions(window.surveyData);
            } else {
                populateCountryOptions(window.surveyData);
            }

            applyFilters();
        }).catch(error => {
            console.error("Error loading the CSV file:", error);
        });
    }

    function populateCountryOptions(data) {
        const countries = Array.from(new Set(data.map(d => d.country).filter(c => c && c.trim() !== ''))).sort();
        countryFilter.querySelectorAll('option:not([value="all"])').forEach(opt => opt.remove());
        countries.forEach(c => {
            const option = document.createElement('option');
            option.value = c.toLowerCase();
            option.textContent = c;
            countryFilter.appendChild(option);
        });
    }

    resetFiltersBtn.addEventListener('click', () => {
        countryFilter.value = 'all';
        genderFilter.value = 'all';
        ageRange.value = 80;
        ageValue.textContent = 'Up to 80';
        applyFilters();
    });

    applyFiltersBtn.addEventListener('click', () => {
        applyFilters();
    });

    function applyFilters() {
        if (!window.surveyData || window.surveyData.length === 0) {
            console.warn('No data loaded yet');
            return;
        }

        const countryVal = countryFilter.value.toLowerCase();
        const genderVal = genderFilter.value.toLowerCase();
        const ageVal = +ageRange.value;

        const filteredData = window.surveyData.filter(d => {
            if (countryVal !== 'all' && (!d.country || d.country.toLowerCase() !== countryVal)) return false;
            if (genderVal !== 'all' && (!d.gender || d.gender.toLowerCase() !== genderVal)) return false;
            if (d.age === null || d.age > ageVal) return false;
            return true;
        });

        createBarChart(filteredData, 'mental_health_consequence', '#mental-consequence-chart', 'Mental Health Consequences');
        createBarChart(filteredData, 'phys_health_consequence', '#physical-consequence-chart', 'Physical Health Consequences');
        createBarChart(filteredData, 'mental_health_interview', '#interview-comparison-chart', 'Interview Discussion Comparison');
        createBarChart(filteredData, 'coworkers', '#coworkers-chart', 'Coworker Discussions');
        createBarChart(filteredData, 'mental_vs_physical', '#employer-perception-chart', 'Employer Perception');
    }

    function createBarChart(data, column, container, title) {
        const margin = { top: 40, right: 20, bottom: 60, left: 60 };
        const containerWidth = d3.select(container).node().clientWidth;
        const width = containerWidth - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;

        d3.select(container).selectAll('*').remove();

        const svg = d3.select(container)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "chart-svg")
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Count frequency
        const counts = {};
        data.forEach(d => {
            const value = d[column] || "Unknown";
            counts[value] = (counts[value] || 0) + 1;
        });

        const entries = Object.entries(counts).map(([key, value]) => ({ key, value }));

        // Sort by value descending
        entries.sort((a, b) => b.value - a.value);

        // Scales
        const x = d3.scaleBand()
            .domain(entries.map(d => d.key))
            .range([0, width])
            .padding(0.3);

        const y = d3.scaleLinear()
            .domain([0, d3.max(entries, d => d.value)])
            .nice()
            .range([height, 0]);

        // Grid lines
        svg.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(-width)
                .tickFormat("")
            )
            .selectAll("line")
            .attr("stroke", "var(--gray-color)")
            .attr("stroke-dasharray", "2,2")
            .attr("opacity", 0.5);

        // Bars with modern styling
        svg.selectAll(".bar")
            .data(entries)
            .enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", d => x(d.key))
            .attr("y", d => y(d.value))
            .attr("width", x.bandwidth())
            .attr("height", d => height - y(d.value))
            .attr("rx", 4)
            .attr("ry", 4)
            .attr("fill", column.includes('mental') ? "var(--primary-color)" : "var(--accent-color)");

        // Value labels on bars
        svg.selectAll(".bar-label")
            .data(entries)
            .enter()
            .append("text")
            .attr("x", d => x(d.key) + x.bandwidth() / 2)
            .attr("y", d => y(d.value) - 5)
            .attr("text-anchor", "middle")
            .attr("font-size", "12px")
            .attr("font-weight", "500")
            .attr("fill", "var(--dark-color)")
            .text(d => d.value);

        // X Axis with improved styling
        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .attr("class", "axis")
            .call(d3.axisBottom(x))
            .selectAll("text")
            .attr("transform", "rotate(-25)")
            .style("text-anchor", "end")
            .attr("dx", "-0.5em")
            .attr("dy", "0.5em")
            .attr("font-size", "11px");

        // Y Axis with better styling
        svg.append("g")
            .attr("class", "axis")
            .call(d3.axisLeft(y).ticks(5))
            .selectAll("text")
            .attr("font-size", "11px");

        // Chart title
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", -15)
            .attr("text-anchor", "middle")
            .attr("font-weight", "600")
            .attr("font-size", "14px")
            .attr("fill", "var(--dark-color)")
            .text(title);
    }

    initPage();
});