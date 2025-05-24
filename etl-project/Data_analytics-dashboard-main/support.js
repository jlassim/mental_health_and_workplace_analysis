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

    function initPage() {
        d3.csv('final_data.csv').then(data => {
            // Clean and normalize data
            window.surveyData = data.map(row => {
                row.age = row.age ? +row.age : null;
                
                if (row.gender) {
                    const g = row.gender.toLowerCase();
                    if (g.includes('female')) row.gender = 'female';
                    else if (g.includes('male')) row.gender = 'male';
                    else row.gender = 'other';
                } else {
                    row.gender = 'other';
                }
                
                // Clean support-related fields
                row.benefits = row.benefits ? row.benefits.trim() : 'Unknown';
                row.care_options = row.care_options ? row.care_options.trim() : 'Unknown';
                row.wellness_program = row.wellness_program ? row.wellness_program.trim() : 'Unknown';
                row.seek_help = row.seek_help ? row.seek_help.trim() : 'Unknown';
                row.anonymity = row.anonymity ? row.anonymity.trim() : 'Unknown';
                row.leave = row.leave ? row.leave.trim() : 'Unknown';
                
                return row;
            });

            if (typeof window.commonPopulateCountryOptions === 'function') {
                window.commonPopulateCountryOptions(window.surveyData);
            } else {
                populateCountryOptions(window.surveyData);
            }

            // Initialize gender filter options
            const genders = ['All', 'Male', 'Female', 'Other'];
            genderFilter.innerHTML = '<option value="all">All Genders</option>';
            genders.forEach(g => {
                const option = document.createElement('option');
                option.value = g.toLowerCase();
                option.textContent = g;
                genderFilter.appendChild(option);
            });

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

        renderVerticalBarChart(filteredData, 'benefits-chart', 'benefits', 'Mental Health Benefits');
        renderVerticalBarChart(filteredData, 'care-options-chart', 'care_options', 'Knowledge of Care Options');
        renderVerticalBarChart(filteredData, 'wellness-program-chart', 'wellness_program', 'Wellness Program Inclusion');
        renderVerticalBarChart(filteredData, 'resources-chart', 'seek_help', 'Employer Resources');
        renderVerticalBarChart(filteredData, 'anonymity-chart', 'anonymity', 'Anonymity Protection');
        renderVerticalBarChart(filteredData, 'leave-chart', 'leave', 'Medical Leave Accessibility');
    }

    function renderVerticalBarChart(data, containerId, field, title) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = { top: 40, right: 20, bottom: 60, left: 60 };
        const containerWidth = container.node().clientWidth;
        const width = containerWidth - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;

        const svg = container.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "chart-svg")
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Group and count data
        const groupedData = d3.rollups(data, v => v.length, d => d[field])
                            .filter(d => d[0] && d[0].trim() !== '') // Remove empty responses
                            .sort((a, b) => b[1] - a[1]); // Sort by count descending

        const x = d3.scaleBand()
            .domain(groupedData.map(d => d[0]))
            .range([0, width])
            .padding(0.3);

        const y = d3.scaleLinear()
            .domain([0, d3.max(groupedData, d => d[1])])
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
            .data(groupedData)
            .enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", d => x(d[0]))
            .attr("y", d => y(d[1]))
            .attr("width", x.bandwidth())
            .attr("height", d => height - y(d[1]))
            .attr("rx", 4)
            .attr("ry", 4)
            .attr("fill", (d, i) => {
                // Use different colors for different categories
                const colors = ['var(--primary-color)', 'var(--secondary-color)', 'var(--accent-color)', 'var(--success-color)'];
                return colors[i % colors.length];
            });

        // Value labels on bars
        svg.selectAll(".bar-label")
            .data(groupedData)
            .enter()
            .append("text")
            .attr("x", d => x(d[0]) + x.bandwidth() / 2)
            .attr("y", d => y(d[1]) - 8)
            .attr("text-anchor", "middle")
            .attr("font-size", "12px")
            .attr("font-weight", "500")
            .attr("fill", "var(--dark-color)")
            .text(d => d[1]);

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