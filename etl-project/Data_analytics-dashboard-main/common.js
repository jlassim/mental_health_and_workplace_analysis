// common.js
document.addEventListener('DOMContentLoaded', () => {
  const applyFiltersBtn = document.getElementById('apply-filters');
  const ageInput = document.getElementById('age');
  const ageValue = document.getElementById('age-value');
  const countrySelect = document.getElementById('country');
  const toast = document.getElementById('toast');

  // surveyData is expected to be set globally by index.js after CSV load
  // So here, just declare it (do NOT initialize or load CSV)
  window.surveyData = window.surveyData || [];

  ageInput.addEventListener('input', () => {
    ageValue.textContent = ageInput.value;
  });

  // Populate country dropdown when surveyData is ready
  function populateCountryOptions(data) {
    const countries = Array.from(new Set(data.map(d => d.country).filter(c => c && c.trim() !== '')));
    countries.sort();

    countries.forEach(country => {
      const option = document.createElement('option');
      option.value = country;
      option.textContent = country;
      countrySelect.appendChild(option);
    });
  }

  // Expose a function for index.js to call after CSV load
  window.commonPopulateCountryOptions = populateCountryOptions;

  // Filter button
  applyFiltersBtn.addEventListener('click', () => {
    applyFilters();
  });

  function applyFilters() {
    const genderFilter = document.getElementById('gender').value;
    const ageFilter = +document.getElementById('age').value;
    const countryFilter = document.getElementById('country').value;
    const remoteFilter = document.getElementById('remote').value;
    const techFilter = document.getElementById('tech').value;

    let filtered = window.surveyData.filter(d => {
      if (genderFilter !== 'All' && d.gender !== genderFilter) return false;
      if (countryFilter !== 'All' && d.country !== countryFilter) return false;
      if (remoteFilter !== 'All' && d.remote_work !== remoteFilter) return false;
      if (techFilter !== 'All' && d.tech_company !== techFilter) return false;
      if (d.age === null || d.age > ageFilter) return false;
      return true;
    });

    // Update the summary metrics and charts using functions from index.js
    if (window.updateCharts) {
      window.updateCharts(filtered);
    }

    showToast("Filters applied successfully!");
  }

  function showToast(message) {
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => {
      toast.style.display = 'none';
    }, 3000);
  }
});
