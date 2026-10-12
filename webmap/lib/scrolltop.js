/** Scroll to Top, from: https://coursesweb.net/javascript/ **/

var scrTop = new Object();
 // function to get scrollbar vertical position
 scrTop.scrollY = function() {
 return window.pageYOffset ? window.pageYOffset : document.documentElement.scrollTop ? document.documentElement.scrollTop : document.body.scrollTop;
 }

 // gets the height of the window
 scrTop.brows_height = function() {
 if (self.innerHeight) {
 var brows_hgh = self.innerHeight;
 } else if (document.documentElement && document.documentElement.clientHeight) {
 var brows_hgh = document.documentElement.clientHeight;
 } else if (document.body) {
 var brows_hgh = document.body.clientHeight;
 }
 return brows_hgh;
 }

 // function for register event on scroll window
 scrTop.onScrollWin = function() {
 // if exists in page the #sttop element
 if(document.getElementById('sttop')) {
 window.onscroll = function() {
 var scrl_pos = scrTop.scrollY(); // get vertical scrollbar position

 // if vertical scroll position is more then half of brows_height, and no element '#scrtop'
 // add button to scroll to Top of the page as child element in #sttop
 // else, if vertical scroll position is less half of brows_height, and element '#scrtop'
 // remove button to scroll to Top of the page
 if(scrl_pos > (scrTop.brows_height() *.5) && !document.getElementById('scrtop')) {
 document.getElementById('sttop').innerHTML = '<div id="scrtop" onclick="window.scrollTo(0,0)"><span>&uArr;</span>TOP</div>';
 }
 else if(scrl_pos < (scrTop.brows_height() *.5) && document.getElementById('scrtop')) {
 document.getElementById('sttop').removeChild(document.getElementById('scrtop'));
 }
 }
 }
 }
scrTop.onScrollWin();