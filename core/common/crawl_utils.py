def gen_download_script(url: str, filename: str) -> str:
    """生成下载文件的脚本"""
    return """
        async function downloadFile(fileUrl, filename){
            try{
                const response = await fetch(fileUrl);
                if (!response.ok){
                    throw new Error('FailDownload');
                }
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error(error);
            }
        }
        const downloadUrl = '%s';
        const downloadName = '%s';
        downloadFile(downloadUrl, downloadName); 
    """ % (url, filename)

def gen_url_download_script(url):
    return """
        const link = document.createElement('a');
        link.href = '%s';
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    """%url