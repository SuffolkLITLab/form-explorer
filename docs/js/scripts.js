
/*-----------------------------------------------------------------

     FUNCTIONS FROM https://github.com/turbomaze/word2vecjson

-----------------------------------------------------------------*/

function getCosSim(f1, f2) {
  return Math.abs(f1.reduce(function(sum, a, idx) {
    return sum + a*f2[idx];
  }, 0)/(mag(f1)*mag(f2))); //magnitude is 1 for all feature vectors
}

function mag(a) {
  return Math.sqrt(a.reduce(function(sum, val) {
    return sum + val*val;
  }, 0));
}

function norm(a) {
  var a_mag = mag(a);
  return a.map(function(val) {
    return val/a_mag;
  });
}

/*-----------------------------------------------------------------

       Auto complete adapted from https://www.w3schools.com/howto/howto_js_autocomplete.asp

  -----------------------------------------------------------------*/

  function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();

        if (!val) { return false;}
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);

        if ($("#mode_1").is(":checked")) {
          var nresults = 0;
          /*for each item in the array...*/
          for (i = 0; i < arr.length; i++) {
            /*check if the item starts with the same letters as the text field value:*/
            if (arr[i].toUpperCase().match(val.toUpperCase())) {
              /*create a DIV element for each matching element:*/
              b = document.createElement("DIV");
              /*make the matching letters bold:*/
              var pos = arr[i].toUpperCase().match(val.toUpperCase()).index
              b.innerHTML = arr[i].substr(0,pos);
              b.innerHTML += "<strong>" + arr[i].substr(pos, val.length) + "</strong>";
              b.innerHTML += arr[i].substr(pos + val.length);
              /*insert a input field that will hold the current array item's value:*/
              b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
              /*execute a function when someone clicks on the item value (DIV element):*/
              b.addEventListener("click", function(e) {
                  /*insert the value for the autocomplete text field:*/
                  // OLD inp.value = this.getElementsByTagName("input")[0].value;
                  inp.value = this.innerText;
                  /*close the list of autocompleted values,
                  (or any other open lists of autocompleted values:*/
                  closeAllLists();
              });
              a.appendChild(b);
              nresults++;
            }
            if (nresults > 10){
              break;
            }
          }
        }

    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
          /*If the arrow DOWN key is pressed,
          increase the currentFocus variable:*/
          currentFocus++;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 38) { //up
          /*If the arrow UP key is pressed,
          decrease the currentFocus variable:*/
          currentFocus--;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 13) {
          /*If the ENTER key is pressed, prevent the form from being submitted,*/
          e.preventDefault();
          if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
          }
        }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
          x[i].parentNode.removeChild(x[i]);
        }
      }
    }
    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
  }



    /*-----------------------------------------------------------------

         NEW FUNCTIONS

    -----------------------------------------------------------------*/


    function updateDB() {
      var FormsFiltered = filterStates();
      var FormNames = FormsFiltered.map(function (el) { return el.name; })
      autocomplete(document.getElementById("q"), FormNames);
    }

    function getStates() {
      var selected = [];
      $('#checkboxes input:checked').each(function() {
          selected.push($(this).attr('id'));
      });
      return selected
    }

    function getFormID(title) {
      FormsFiltered = filterStates();
      x = FormsFiltered.filter((item)=>{
        return Object.keys(item).some((key)=>item["name"].toLowerCase().trim()==title.toLowerCase().trim())
      })[0];
      if (x===undefined){
        return false
      } else {
        return x;
      }
    }

    function filterbyID(fid) {
        return FormsInfo.filter((item)=>{
          return Object.keys(item).some((key)=>item["fid"].includes(fid))
        })[0];
    }

    function filterStates() {
        return FormsInfo.filter((item)=>{
          var output = 0;
          var states = getStates();
          //console.log(item)
          for (state in states) {
            if (Object.keys(item).some((key)=>item["jur"].includes(states[state]))) {
              output = 1;
            }
          }
          if (output == 1) {
            return true
          } else {
            return false
          }
        });
    }

    function addforms(){
      $('#search_results option:selected').remove().appendTo('#compare_me');
    }

    function removeforms(){
      $('#compare_me option:selected').remove().appendTo('#search_results');
    }

    function openforms(){
      var output = ""
      var selected = $("#search_results :selected").map((_, e) => e.value).get();
      for (item in selected) {
        //alert("We're still moving over the new library. 24K forms is a lot. This feature will be available in a few days.");  
        window.open("https://suffolklitlab.org/form-explorer/form/"+filterbyID(selected[item])["jur"]+"/"+selected[item]+".html", "_blank");
      }
    }


    function compareforms(){
      var output = ""
      var selected = $("#compare_me option").map(function() {return $(this).val();}).get()
      if (selected.length < 2) {
        alert('You need at least two forms in this list before we can make a comparison.')
      } else {
        var i = 1
        for (item in selected) {
          output += selected[item];
          if (i<selected.length) {
            output += ",";
          } else {
            output += "";
          }
          i +=1;
        }
        window.open("side-by-side/index.html?ids="+output, "_blank");
      }
    }

    function run_search(val) {

      var n = 1000;
      localStorage.cutoff = $('#cutoff').val();
      answers = [];
      if (val.trim().length> 0) {

        var nresults = 0;
        var FormsFiltered = filterStates();
        if ($("#mode_1").is(":checked")) {
          var fvec = getFormID(val)["vec"]
          //console.log("fvec",fvec)
          if (fvec != undefined) {
            for (var ans in FormsFiltered) {
              var sim = getCosSim(fvec, FormsFiltered[ans]["vec"]);
              //console.log(sim)
              if (sim>=$('#cutoff').val()/100) {
                answers.push([sim,FormsFiltered[ans]["fid"],FormsFiltered[ans]["jur"],FormsFiltered[ans]["name"]]);
                nresults++;
              }
            }
            answers.sort(function(a, b) {
              return b[0] - a[0];
            });
            $('#resultN').html(answers.length)
            return answers
            //return answers.slice(0, n);
          } else {
            alert("No form with that name found for the selected jurisdictions. Consider trying a free text search.")
          }
        } else if ($("#mode_2").is(":checked")) {
          if (val.replace(/\s{2,}/g,' ').trim().length >= 3) {
            for (var ans in FormsFiltered) {
              //console.log(FormsFiltered[ans]["text"])
              if (FormsFiltered[ans]["text"].trim().toUpperCase().includes(val.trim().toUpperCase())) {
                //console.log(ans)
                answers.push([1,FormsFiltered[ans]["fid"],FormsFiltered[ans]["jur"],FormsFiltered[ans]["name"]]);
                nresults++;
              }
            }
          } else {
            alert("Your text search must be at least 3 characters long.")
          }
          $('#resultN').html(answers.length)
          return answers
        }

      } else {
        $('#resultN').html(answers.length)
        return answers
      }
    }

    function test_understanding(string) {
      $("#loading").empty();
      $('#loading').show();
      $("#search_results").empty();
      start_spinner('loading');

      // getNClosestAnswer allows for the return of multiple labels
      // here we've limited it to one. Additionally, we're filtering by
      // QLabels to apply consistent labels. To allow for multiple instances
      // of the same labels we append a #n to the label. This removes that.

      setTimeout(function (){

        answers = run_search(string);
        $('#loading_cites').html("");
        $('#loading').hide();

        for (var result in answers){
          //console.log(answers[result][0])
          $('#search_results').append($('<option>', {
              value: answers[result][1],
              text: answers[result][3]
          }));
        }

      }, 50);

    }

    function start_spinner(target_id) {
      var opts = {
        lines: 13, // The number of lines to draw
        length: 7, // The length of each line
        width: 4, // The line thickness
        radius: 10, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        color: '#000', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
      };
      var target = document.getElementById(target_id);
      var spinner = new Spinner(opts).spin(target);
    }

    function preload(arrayOfImages) {
        $(arrayOfImages).each(function () {
            console.log("Loading: "+this)
            $('<img />').attr('src',this).appendTo('body').css('display','none');
        });
    }

    function pick_image(path="../") {
      var i = Math.floor(Math.random() * 9) + 1;
      if (i==1) {
        $("#patience").attr("src",path+"images/alice.webp");
      } else if (i==2) {
        $("#patience").attr("src",path+"images/bean.gif");
      } else if (i==3) {
        $("#patience").attr("src",path+"images/jimmy.gif");
      } else if (i==4) {
        $("#patience").attr("src",path+"images/little_r.webp");
      } else if (i==5) {
        $("#patience").attr("src",path+"images/patience.gif");
      } else if (i==6) {
        $("#patience").attr("src",path+"images/pbride.webp");
      } else if (i==7) {
        $("#patience").attr("src",path+"images/seinfeld.gif");
      } else if (i==8) {
        $("#patience").attr("src",path+"images/ted.gif");
      } else if (i==9) {
        $("#patience").attr("src",path+"images/twinpeaks.gif");
      }
    }

    jQuery.cachedScript = function( url, options ) {

      // Allow user to set any option except for dataType, cache, and url
      options = $.extend( options || {}, {
        dataType: "script",
        cache: true,
        url: url
      });

      // Use $.ajax() since it is more flexible than $.getScript
      // Return the jqXHR object so we can chain callbacks
      return jQuery.ajax( options );
    };

    function load_list_find (path="../") {
      console.log("loading DB...");
      pick_image(path);
      $('#msg').show();

      $('#content').hide();
      $('#output').html("Loading tens of thousands of forms...");

      // Usage

      $.cachedScript( "https://courtformsonline.org/js_bin/formsinfo.js" ).done(function( script, textStatus ) {
      //$.cachedScript( "https://suffolklitlab.org/form-explorer/js/formsinfo.js" ).done(function( script, textStatus ) {
      //$.cachedScript( "https://findmycite.org/js/word2vec.js?=2022-08-22" ).done(function( script, textStatus ) {
        console.log( textStatus );

        $('#content').show();
        $('#msg').hide();
        $('#output').html("Thinking...")

        updateDB();

      });
    }


    function load_list_compare (path="../../") {
      console.log("loading DB...");
      $('#msg').show();
      start_spinner('msg');

      $('#content').hide();

      // Usage

      $.cachedScript( "https://courtformsonline.org/js_bin/formsinfo.js" ).done(function( script, textStatus ) {
      //$.cachedScript( "https://suffolklitlab.org/form-explorer/js/formsinfo.js" ).done(function( script, textStatus ) {
      //$.cachedScript( "https://findmycite.org/js/word2vec.js?=2022-08-22" ).done(function( script, textStatus ) {
        console.log( textStatus );

        $('#content').show();
        $('#msg').hide();

        build_table();

      });
    }



    const params = new Proxy(new URLSearchParams(window.location.search), {
      get: (searchParams, prop) => searchParams.get(prop),
    });
    // Get the value of "some_key" in eg "https://example.com/?some_key=some_value"

    function getStandardDeviation (array) {
      const n = array.length
      const mean = array.reduce((a, b) => a + b) / n
      return Math.sqrt(array.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / n)
    }

    function build_table() {
      var ids = params.ids.split(",");
      //console.log("load ids",ids)
      var html = "<table border='1' width='100%'>"

      html += "</tr><tr><td colspan='"+(ids.length+1)+"' bgcolor='#eee'><b>General Info.</b></td>"

      html += "<tr><td>Title</td>"
      // names
      for (id in ids) {
        //html += "<td><a href='javascript:alert(`We are still moving over the new library. 24K forms is a lot. This feature will be available in a few days.`);'>"+filterbyID(ids[id])["name"]+"</a></td>"
        html += "<td><a href='../../form/"+filterbyID(ids[id])["jur"]+"/"+filterbyID(ids[id])["fid"]+".html' target='_blank'>"+filterbyID(ids[id])["name"]+"</a></td>"
      }

      var array = []
      for (id in ids) {
        array = array.concat(filterbyID(ids[id])["reading"]);
      }
      mean = (array.reduce((a, b) => a + b) / array.length).toFixed(2);
      std = getStandardDeviation(array).toFixed(2)
      html += "</tr><tr><td>Reading Level<br><font size=-1>Mean "+mean+", Std. " +std+"</font></td>"
      for (id in ids) {
        var metric = filterbyID(ids[id])["reading"]
        if (metric<=(1*mean-1*std)){
          html += "<td bgcolor='#66ff66'>"
        } else if (metric>=(1*mean+2*std)) {
          html += "<td bgcolor='#ef6161'>"
        } else if (metric>=(1*mean+1*std)) {
          html += "<td bgcolor='#fdfd66'>"
        } else {
          html += "<td>"
        }
        html += metric+"</td>"
      }


      var array = []
      for (id in ids) {
        array = array.concat(filterbyID(ids[id])["pages"]);
      }
      mean = (array.reduce((a, b) => a + b) / array.length).toFixed(2);
      std = getStandardDeviation(array).toFixed(2)
      html += "</tr><tr><td>Pages<br><font size=-1>Mean "+mean+", Std. " +std+"</font></td>"
      for (id in ids) {
        var metric = filterbyID(ids[id])["pages"]
        if (metric<=(1*mean-1*std)){
          html += "<td bgcolor='#66ff66'>"
        } else if (metric>=(1*mean+2*std)) {
          html += "<td bgcolor='#ef6161'>"
        } else if (metric>=(1*mean+1*std)) {
          html += "<td bgcolor='#fdfd66'>"
        } else {
          html += "<td>"
        }
        html += metric+"</td>"
      }

      var array = []
      for (id in ids) {
        array = array.concat(filterbyID(ids[id])["fields"].length);
      }
      mean = (array.reduce((a, b) => a + b) / array.length).toFixed(2);
      std = getStandardDeviation(array).toFixed(2)
      html += "</tr><tr><td>Fields<br><font size=-1>Mean "+mean+", Std. " +std+"</font></td>"
      for (id in ids) {
        var metric = filterbyID(ids[id])["fields"].length
        if (metric<=(1*mean-1*std)){
          html += "<td bgcolor='#66ff66'>"
        } else if (metric>=(1*mean+2*std)) {
          html += "<td bgcolor='#ef6161'>"
        } else if (metric>=(1*mean+1*std)) {
          html += "<td bgcolor='#fdfd66'>"
        } else {
          html += "<td>"
        }
        html += metric+"</td>"
      }

      var array = []
      for (id in ids) {
        array = array.concat(filterbyID(ids[id])["f_per_p"]);
      }
      mean = (array.reduce((a, b) => a + b) / array.length).toFixed(2);
      std = getStandardDeviation(array).toFixed(2)
      html += "</tr><tr><td>Fields per Page<br><font size=-1>Mean "+mean+", Std. " +std+"</font></td>"
      for (id in ids) {
        var metric = filterbyID(ids[id])["f_per_p"].toFixed(2)
        if (metric<=(1*mean-1*std)){
          html += "<td bgcolor='#66ff66'>"
        } else if (metric>=(1*mean+2*std)) {
          html += "<td bgcolor='#ef6161'>"
        } else if (metric>=(1*mean+1*std)) {
          html += "<td bgcolor='#fdfd66'>"
        } else {
          html += "<td>"
        }
        html += metric+"</td>"
      }

      //html += "</tr><tr><td>Court Applied Label</td>"
      //for (id in ids) {
      //  html += "<td><a href='../../list/"+filterbyID(ids[id])["jur"]+"/#"+filterbyID(ids[id])["label"].replaceAll(/[^a-z0-9]+/gi,"_")+"' target='_blank'>"+filterbyID(ids[id])["label"]+"</a></td>"
      //}

      var all_list = []
      for (id in ids) {
        all_list = all_list.concat(filterbyID(ids[id])["list"]);
      }
      all_list = [...new Set(all_list)]
      html += "</tr><tr><td colspan='"+(ids.length+1)+"' bgcolor='#eee'><b>List Codes ("+all_list.length+")</b></td>"

      if (all_list.length==0){
        html += "</tr><tr><td colspan='"+(ids.length+1)+"'><i>None Found</i></td>"
      }

      for (field in all_list) {
        html += "</tr><tr><td><a href='https://taxonomy.legal/term/"+all_list[field]+"' target='_blank'>"+all_list[field]+"</a>"
        for (id in ids) {
          if (filterbyID(ids[id])["list"].includes(all_list[field])) {
            html += "<td bgcolor='#66ff66'> &check;"
          } else {
            html += "<td> "
          }
          html += "</td>"
        }
      }

      var all_fields = []
      for (id in ids) {
        all_fields = all_fields.concat(filterbyID(ids[id])["fields"]);
      }
      all_fields = [...new Set(all_fields)]
      html += "</tr><tr><td colspan='"+(ids.length+1)+"' bgcolor='#eee'><b>Unique Fields ("+all_fields.length+")</b></td>"

      for (field in all_fields) {
        html += "</tr><tr><td>"+all_fields[field]
        for (id in ids) {
          if (filterbyID(ids[id])["fields"].includes(all_fields[field])) {
            html += "<td bgcolor='#66ff66'> &check;"
          } else {
            html += "<td> "
          }
          html += "</td>"
        }
      }


      html += "</tr></table>"
      $('#data').html(html)
    }
