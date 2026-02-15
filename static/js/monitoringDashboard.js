console.log("monitoringDashboard.js loaded ......")

const tabs = document.querySelectorAll('[role="tab"]');

tabs.forEach(tab => {
	tab.addEventListener('click', () => {
		tabs.forEach(t => {
			t.setAttribute('aria-selected', 'false');
			document.getElementById(t.getAttribute('aria-controls')).hidden = true;
		});

		tab.setAttribute('aria-selected', 'true');
		document.getElementById(tab.getAttribute('aria-controls')).hidden = false;
	});
});
