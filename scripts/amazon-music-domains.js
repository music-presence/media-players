// To get all domains for Amazon Music:
// 1. Visit https://en.wikipedia.org/wiki/Amazon_(company)#Website
// 2. Open a developer tools console
// 3. Paste the following snippet:
[...new Set([...document.querySelectorAll('table tbody td')]
    .map(element => element.innerText.trim().toLowerCase())
    .filter(domain => /^amazon\.[\.a-z]+$/.test(domain))
    .map(reverseDomain => 'music.' + reverseDomain))]
    .sort()
    .join('\n')

// To reverse the domains, add:
// .map(domain => domain.split('.').map(t => t.trim()).reverse().join('.'))
