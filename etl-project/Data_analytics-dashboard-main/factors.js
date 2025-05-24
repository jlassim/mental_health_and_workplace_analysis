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
        row.age = row.age ? +row.age : null;
        if (row.gender) {
          const g = row.gender.toLowerCase();
          if (g.includes('female')) row.gender = 'female';
          else if (g.includes('male')) row.gender = 'male';
          else row.gender = 'other';
        } else {
          row.gender = 'other';
        }
        if (row.treatment) {
          const t = row.treatment.toString().toLowerCase();
          row.treatment = (t === '1' || t === 'yes') ? 1 : 0;
        } else {
          row.treatment = 0;
        }
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

    drawFamilyHistoryChart(filteredData);
    drawSelfEmployedChart(filteredData);
    drawTechCompanyChart(filteredData);
    // drawCountryTreatmentChart(filteredData);  // REMOVED this line!
    drawRemoteTreatmentChart(filteredData);
    drawCompanySizeChart(filteredData);
  }

  function countTreatmentByCategory(data, factorKey) {
    const counts = {};
    data.forEach(d => {
      const cat = d[factorKey] || 'Unknown';
      const treated = d.treatment === 1 ? 1 : 0;
      if (!counts[cat]) counts[cat] = { treated: 0, total: 0 };
      counts[cat].treated += treated;
      counts[cat].total += 1;
    });
    return counts;
  }

  // Vertical bar chart function (bars bottom-up)
 // Update the drawBarChart function in factors.js with these style changes:
function drawBarChart(containerId, dataObj, chartTitle) {
    const container = d3.select(`#${containerId}`);
    container.selectAll('*').remove();

    const margin = { top: 40, right: 20, bottom: 60, left: 60 };
    const width = container.node().clientWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const svg = container.append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .attr('class', 'chart-svg');

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const categories = Object.keys(dataObj);
    const rates = categories.map(cat => {
      const treated = dataObj[cat].treated;
      const total = dataObj[cat].total;
      return total ? (treated / total) * 100 : 0;
    });

    const x = d3.scaleBand()
      .domain(categories)
      .range([0, width])
      .padding(0.3);

    const y = d3.scaleLinear()
      .domain([0, d3.max(rates) * 1.1])
      .nice()
      .range([height, 0]);

    // Bars with modern styling
    g.selectAll('.bar')
      .data(categories)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d))
      .attr('width', x.bandwidth())
      .attr('y', (d, i) => y(rates[i]))
      .attr('height', (d, i) => height - y(rates[i]))
      .attr('rx', 4) // Rounded corners
      .attr('ry', 4) // Rounded corners
      .attr('fill', 'var(--primary-color)');

    // Labels on top of bars with better styling
    g.selectAll('.label')
      .data(categories)
      .enter()
      .append('text')
      .attr('x', d => x(d) + x.bandwidth() / 2)
      .attr('y', (d, i) => y(rates[i]) - 8)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', 'var(--dark-color)')
      .text((d, i) => `${rates[i].toFixed(1)}%`);

    // X Axis with improved styling
    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .attr('class', 'axis')
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "rotate(-25)")
      .style("text-anchor", "end")
      .attr('dx', '-0.5em')
      .attr('dy', '0.5em')
      .attr('font-size', '11px');

    // Y Axis with percentage and better styling
    g.append('g')
      .attr('class', 'axis')
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => d + '%'))
      .selectAll("text")
      .attr('font-size', '11px');

    // Grid lines for better readability
    g.append('g')
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

    // Chart title with modern styling
    svg.append('text')
      .attr('x', (width + margin.left + margin.right) / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('font-weight', '600')
      .attr('font-size', '14px')
      .attr('fill', 'var(--dark-color)')
      .text(chartTitle);
}

  function drawFamilyHistoryChart(data) {
    const counts = countTreatmentByCategory(data, 'family_history');
    drawBarChart('family-history-chart', counts, 'Family History Impact on Treatment');
  }

  function drawSelfEmployedChart(data) {
    const counts = countTreatmentByCategory(data, 'self_employed');
    drawBarChart('self-employed-chart', counts, 'Self-Employment vs Treatment');
  }

  function drawTechCompanyChart(data) {
    const counts = countTreatmentByCategory(data, 'tech_company');
    drawBarChart('tech-company-chart', counts, 'Tech Company Impact on Treatment');
  }

  // REMOVED drawCountryTreatmentChart

  function drawRemoteTreatmentChart(data) {
    const counts = countTreatmentByCategory(data, 'remote_work');
    drawBarChart('remote-treatment-chart', counts, 'Remote Work vs Treatment');
  }

  function drawCompanySizeChart(data) {
    const counts = countTreatmentByCategory(data, 'no_employees');
    drawBarChart('company-size-chart', counts, 'Company Size Impact on Treatment');
  }

  initPage();
});
