// Print a stable text version of each answer; no storage or network requests.
function preparePrint(){document.querySelectorAll('textarea').forEach(field=>{let output=field.nextElementSibling;if(!output||!output.classList.contains('print-answer')){output=document.createElement('div');output.className='print-answer';field.after(output)}output.textContent=field.value||'________________________________________________________________\n\n________________________________________________________________';});}
window.addEventListener('beforeprint',preparePrint);
document.querySelectorAll('textarea').forEach(field=>field.addEventListener('input',preparePrint));
preparePrint();
