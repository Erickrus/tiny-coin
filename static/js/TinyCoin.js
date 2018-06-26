var method = "GET";
function onBlocksClick(){
	$("#url").html("/blocks");
	document.getElementById('textInput').value = '';
	$("#textOutput").html('');
	method = "GET";
}

function onPingClick(){
	$("#url").html("/ping");
	document.getElementById('textInput').value = '';
	$("#textOutput").html('');
	method = "GET";
}

function onMineClick(){
	$("#url").html("/mine");
	document.getElementById('textInput').value = '';
	$("#textOutput").html('');
	method = "GET";
}

function onConsensusClick(){
	$("#url").html("/consensus");
	document.getElementById('textInput').value = '';
	$("#textOutput").html('');
	method = "GET";
}

function onTransactionClick(){
	$("#url").html("/txion");
	document.getElementById('textInput').value = '{"from":"'+minerAddress+'", "to":"'+minerAddress+'", "amount":1}';
	$("#textOutput").html('');
	method = "POST";
}

function onPowClick() {
	$("#url").html("/pow");
	document.getElementById('textInput').value = '{"proof-from":"", "last-proof":9}';
	$("#textOutput").html('');
	method = "POST";
}

function onSubmitClick(){
	var url = $("#url").html();
	var data = document.getElementById('textInput').value;
	console.log(data);

	$.ajax({
		  type: method,
		  url: url,
		  data: data,
		  contentType: 'application/json;charset=UTF-8',
		  success: function(data) {
			  $("#textOutput").html(data)
		  },
	});
}


