form = document.getElementById("login")
form.addEventListener('submit', do_login)

function do_login(event) {
    event.preventDefault
    //get salt from server
    username = form.username.value
    password = form.password.value
    next = form.next.value
    salt = ''
    xhr = new XMLHttpRequest();
    xhr.open('GET','/salt?username='+username,true);
    xhr.onreadystatechange = function(){
        if(xhr?.readyState == 4 && xhr.status == 200){
            salt = xhr.responseText;
            //hash password
            hash = dcodeIO.bcrypt.hashSync(password,salt);
            //redirect
            window.location.assign('/login?username='+username+'&password='+hash+'&next='+next)
            window.location.assign('/login?username='+username+'&password='+hash+'&next='+next)
            /*
            rq = new XMLHttpRequest();
            rq.open('GET','/login?username='+username+'&password='+hash,false);
            rq.onreadystatechange = function(){
                if(rq?.readyState == 4 && rq.status == 200){
                    console.info("login success");
    
                } else if (rq?.readyState == 4 && rq.status == 302) {
                    console.info("login success");
                    window.location.reload()
    
                } else if(rq?.readyState == 4){
                    alert('Wrong username or password');
                }
            }
            rq.send();
            */
        } else if(xhr?.readyState == 4){
            alert('Error: '+xhr.status);
        }
    }
    xhr.send();
}
