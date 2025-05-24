document.addEventListener('DOMContentLoaded', () => {
    const genderFilter = document.getElementById('gender');
    const ageFilter = document.getElementById('age');
    const ageValue = document.getElementById('age-value');
    const countryFilter = document.getElementById('country');
    const remoteFilter = document.getElementById('remote');
    const techFilter = document.getElementById('tech');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const toast = document.getElementById('toast');

    ageFilter.addEventListener('input', () => {
        ageValue.textContent = `Up to ${ageFilter.value}`;
    });

    function showToast() {
        toast.style.display = 'flex';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }

    function initPage() {
        d3.csv("final_data.csv").then(data => {
            window.surveyData = data.map(row => {
                row.age = row.age ? +row.age : null;

                if (row.gender) {
                    const g = row.gender.toLowerCase();
                    if (g.includes('female')) row.gender = 'Female';
                    else if (g.includes('male')) row.gender = 'Male';
                    else row.gender = 'Other';
                } else {
                    row.gender = 'Other';
                }

                return row;
            });

            console.log("Data loaded and normalized:", window.surveyData.slice(0, 5));

            if (typeof window.commonPopulateCountryOptions === 'function') {
                window.commonPopulateCountryOptions(window.surveyData);
            } else {
                populateCountryOptions(window.surveyData);
            }

            updateCharts(window.surveyData);
        }).catch(error => {
            console.error("Error loading the CSV file:", error);
        });
    }

    function populateCountryOptions(data) {
        const countries = Array.from(new Set(data.map(d => d.country).filter(c => c && c.trim() !== ''))).sort();
        countryFilter.querySelectorAll('option:not([value="All"])').forEach(opt => opt.remove());
        countries.forEach(c => {
            const option = document.createElement('option');
            option.value = c;
            option.textContent = c;
            countryFilter.appendChild(option);
        });
    }

    resetFiltersBtn.addEventListener('click', () => {
        genderFilter.value = 'All';
        ageFilter.value = 30;
        ageValue.textContent = 'Up to 30';
        countryFilter.value = 'All';
        remoteFilter.value = 'All';
        techFilter.value = 'All';
        applyFilters();
    });

    applyFiltersBtn.addEventListener('click', () => {
        applyFilters();
        showToast();
    });

    function applyFilters() {
        if (!window.surveyData || window.surveyData.length === 0) {
            console.warn('No data loaded yet');
            return;
        }

        const genderVal = genderFilter.value;
        const ageVal = +ageFilter.value;
        const countryVal = countryFilter.value;
        const remoteVal = remoteFilter.value;
        const techVal = techFilter.value;

        const filteredData = window.surveyData.filter(d => {
            if (genderVal !== 'All' && d.gender !== genderVal) return false;
            if (d.age === null || d.age > ageVal) return false;
            if (countryVal !== 'All' && d.country !== countryVal) return false;
            if (remoteVal !== 'All' && d.remote_work !== remoteVal) return false;
            if (techVal !== 'All' && d.tech_company !== techVal) return false;
            return true;
        });

        updateCharts(filteredData);
    }

    function calculatePercentage(data, key, value) {
        if (data.length === 0) return 0;
        const count = data.filter(d => d[key] && d[key].toString().toLowerCase() === value.toString().toLowerCase()).length;
        return ((count / data.length) * 100).toFixed(1);
    }

    function updateSummaryMetrics(data) {
        const treatmentRate = calculatePercentage(data, 'treatment', '1');
        document.getElementById('treatment-rate').textContent = treatmentRate === '0.0' ? '0.0%' : `${treatmentRate}%`;

        const interferenceData = data.filter(item => item.work_interfere && item.work_interfere.toLowerCase() !== 'never');
        const interferenceRate = interferenceData.length > 0 ? ((interferenceData.length / data.length) * 100).toFixed(1) : 0;
        document.getElementById('interference-rate').textContent = `${interferenceRate}%`;
    }

    function updateCharts(data) {
        updateSummaryMetrics(data);
        createGenderChart(data);
        createCountryChart(data);
        createAgeChart(data);
    }

    function clearChart(containerId) {
        const container = document.getElementById(containerId);
        if (container) container.innerHTML = '';
    }

    function createGenderChart(data) {
        clearChart('gender-chart');

        const counts = { Male: 0, Female: 0, Other: 0 };
        data.forEach(d => {
            if (counts.hasOwnProperty(d.gender)) counts[d.gender]++;
            else counts.Other++;
        });

        const width = 300, height = 300, radius = Math.min(width, height) / 2;
        const svg = d3.select('#gender-chart')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width / 2},${height / 2})`);

        const color = d3.scaleOrdinal()
            .domain(Object.keys(counts))
            .range(['var(--primary-color)', 'var(--accent-color)', 'var(--secondary-color)']);

        const pie = d3.pie().value(d => d[1]);
        const data_ready = pie(Object.entries(counts));

        const arc = d3.arc()
            .innerRadius(0)
            .outerRadius(radius);

        svg.selectAll('path')
            .data(data_ready)
            .join('path')
            .attr('d', arc)
            .attr('fill', d => color(d.data[0]))
            .attr('stroke', 'white')
            .style('stroke-width', '2px')
            .style('opacity', 0.9);

        // Add labels
        svg.selectAll('text')
            .data(data_ready)
            .join('text')
            .text(d => `${d.data[0]}: ${d.data[1]}`)
            .attr('transform', d => {
                const [x, y] = arc.centroid(d);
                // Adjust label position based on slice size
                const mult = 1.2;
                return `translate(${x * mult},${y * mult})`;
            })
            .style('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('font-weight', '500')
            .style('fill', 'var(--dark-color)');
    }

    function createCountryChart(data) {
        clearChart('country-chart');

        const countryCounts = d3.rollup(
            data,
            v => v.length,
            d => d.country || 'Unknown'
        );

        const sortedData = Array.from(countryCounts, ([country, count]) => ({ country, count }))
            .sort((a, b) => b.count - a.count) // Sort descending
            .slice(0, 15); // Show top 15 countries

        const margin = { top: 30, right: 30, bottom: 40, left: 120 };
        const width = document.querySelector('#country-chart').clientWidth - margin.left - margin.right;
        const height = sortedData.length * 30;

        const svg = d3.select('#country-chart')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const x = d3.scaleLinear()
            .domain([0, d3.max(sortedData, d => d.count)])
            .range([0, width]);

        const y = d3.scaleBand()
            .domain(sortedData.map(d => d.country))
            .range([0, height])
            .padding(0.2);

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisTop(x)
                .ticks(5)
                .tickSize(-height)
                .tickFormat('')
            )
            .selectAll('line')
            .attr('stroke', 'var(--gray-color)')
            .attr('stroke-dasharray', '2,2')
            .attr('opacity', 0.5);

        // Bars
        svg.selectAll('.bar')
            .data(sortedData)
            .join('rect')
            .attr('class', 'bar')
            .attr('y', d => y(d.country))
            .attr('height', y.bandwidth())
            .attr('x', 0)
            .attr('width', d => x(d.count))
            .attr('fill', 'var(--primary-color)')
            .attr('rx', 4)
            .attr('ry', 4);

        // X axis
        svg.append('g')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x).ticks(5))
            .selectAll('text')
            .style('font-size', '12px');

        // Y axis
        svg.append('g')
            .call(d3.axisLeft(y))
            .selectAll('text')
            .style('font-size', '13px');

        // Add counts at end of bars
        svg.selectAll('.label')
            .data(sortedData)
            .join('text')
            .attr('class', 'label')
            .attr('x', d => x(d.count) + 5)
            .attr('y', d => y(d.country) + y.bandwidth() / 2)
            .attr('dy', '0.35em')
            .text(d => d.count)
            .style('fill', 'var(--dark-color)')
            .style('font-weight', '600')
            .style('font-size', '12px');
    }

    function createAgeChart(data) {
        clearChart('age-chart');

        const ages = data.map(d => d.age).filter(age => age !== null && !isNaN(age));
        if (ages.length === 0) return;

        const margin = {top: 30, right: 30, bottom: 50, left: 50};
        const width = 400 - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;

        const svg = d3.select('#age-chart')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // X scale: age bins (5-year intervals)
        const x = d3.scaleLinear()
            .domain([d3.min(ages), d3.max(ages)])
            .range([0, width]);

        const histogram = d3.histogram()
            .domain(x.domain())
            .thresholds(x.ticks(Math.floor((d3.max(ages) - d3.min(ages))/5)));

        const bins = histogram(ages);

        const y = d3.scaleLinear()
            .domain([0, d3.max(bins, d => d.length)])
            .nice()
            .range([height, 0]);

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(-width)
                .tickFormat('')
            )
            .selectAll('line')
            .attr('stroke', 'var(--gray-color)')
            .attr('stroke-dasharray', '2,2')
            .attr('opacity', 0.5);

        // Bars
        svg.selectAll('rect')
            .data(bins)
            .join('rect')
            .attr('x', 1)
            .attr('transform', d => `translate(${x(d.x0)},${y(d.length)})`)
            .attr('width', d => x(d.x1) - x(d.x0) - 1)
            .attr('height', d => height - y(d.length))
            .attr('fill', 'var(--accent-color)')
            .attr('rx', 2)
            .attr('ry', 2);

        // X axis
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x).ticks(10))
            .selectAll('text')
            .style('font-size', '12px');

        // Y axis
        svg.append('g')
            .call(d3.axisLeft(y).ticks(5))
            .selectAll('text')
            .style('font-size', '12px');

        // X axis label
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height + margin.bottom - 10)
            .style('text-anchor', 'middle')
            .style('font-size', '13px')
            .text('Age');

        // Y axis label
        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', -margin.left + 15)
            .attr('x', -height/2)
            .style('text-anchor', 'middle')
            .style('font-size', '13px')
            .text('Count');
    }

    // Initialize the page
    initPage();

    // Expose updateCharts globally for common.js to call after filters
    window.updateCharts = updateCharts;
});