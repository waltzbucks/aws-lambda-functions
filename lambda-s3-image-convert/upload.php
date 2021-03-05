<?php
require('vendor/autoload.php');
// this will simply read AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from env vars
$s3 = new Aws\S3\S3Client([
    'version'  => 'latest',
    'region'   => '', // TODO: Input the AWS region e.g. ap-northeast-2
    'credentials' => [
	    'key'    => "",  // TODO: Input the AWS Access Key ID 
	    'secret' => "", // TODO: Input the AWS Secret Access Key
    ]
]);

//$bucket = getenv('S3_BUCKET')?: die('No "S3_BUCKET" config var in found in env!');
$bucket = ""; // TODO: Input S3 Bucket for a user image upload
?>

<html>
    <head><meta charset="UTF-8"></head>
    <style>
        body {
            padding-top: 5px;
            color: #FFFFFF;
            background-color: #343A40;
            background-repeat:no-repeat;
            background-position:top center;
            background-attachment:scroll;
        }
        div.form {
            width: 100%;

        }
        a {
            color: #FFFFFF;
            text-decoration: none;
        }
        a:hover {
            color: #FF0000;
            background-color: #000000;
            text-decoration: none;
        }
        form {
            width: 500px;
            text-align: left;
            background-color: #3CBC8D;
        }
        .browse {
            width: 500px;
            height: 30px;
            background-color: transparent;
            border-width: 1;
            border-style: solid;
            border-color: #FFFFFF;
            font-family: Arial;
            color: #000000;
        }
        .submit {
            width: 80px;
            height: 30px;
            position: absolute;	
            left: 426px;
        
        }
        .fit-picture {
            width: 400px;
        }

    </style>
    <body>
        <div id='fileupload'>
            <h1>S3 upload example</h1>
            <h2>Upload a file</h2>
            <form enctype="multipart/form-data" action="<?=$_SERVER['PHP_SELF']?>" method="POST">
                <input name="userfile" type="file" class="browse"><br>
                <input value="Upload" type="submit" class="submit">
            </form>
            <br>
            <?php

            $mimetype = mime_content_type($_FILES['userfile']['tmp_name']);

            if($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_FILES['userfile']) && $_FILES['userfile']['error'] == UPLOAD_ERR_OK && is_uploaded_file($_FILES['userfile']['tmp_name']) && in_array($mimetype, array('image/jpeg', 'image/gif', 'image/png')) ) {
                try {
                    $FullPathFilename = 'original/'.time().'/'.$_FILES['userfile']['name'];
                    $uploadresult = $s3->putObject(array(
                        'Bucket'     => $bucket,
                        'Key'        => $FullPathFilename,
			            'Body'       => fopen($_FILES['userfile']['tmp_name'], 'rb'),
			            'ACL'    => 'public-read',
                        'ContentType' => $mimetype
                    ));
		    ?><p>Uploaded:<br>&nbsp;&nbsp;&nbsp;&nbsp;Object URL=<?php echo $uploadresult['ObjectURL'];?><br>&nbsp;&nbsp;&nbsp;&nbsp;ETag=<?php echo $uploadresult['ETag'];?></p>
            <p><img class="fit-picture" src="<?php echo $uploadresult['ObjectURL'];?>"/></p>
            <?php
                } catch(Exception $e) {
                    ?><p>Upload error :(</p><?php
                } 
            } else {
                echo 'Upload a real image, jerk!';
            }
            ?>
        </div>
    </body>
</html>
