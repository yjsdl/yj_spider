# -*- coding: utf-8 -*-

from Yjsdl import Spider, item
# from Yjsdl.utils.UserAgent import middleware
from testmidl import middleware


async def retry_func(request):
    request.request_config["TIMEOUT"] = 10


class RetryDemo(Spider):
    request_config = {
        "RETRIES": 3,
        "DELAY": 2,
        "TIMEOUT": 2,
        "RETRY_FUNC": retry_func,
    }

    concurrency = 3

    async def start_requests(self):
        for i in range(0, 1):
            yield self.request(
                url="http://httpbin.org/get"
            )

    async def parse(self, response):
        # print(response)

        aaa = {
            'title_name': 'Mechanism of piR-1245/PIWI-like protein-2 regulating Janus kinase-2/signal transducer and activator of transcription-3/vascular endothelial growth factor signaling pathway in retinal neovascularization',
            'author': 'Yong Yu;Li-Kun Xia;Yu Di;Qing-Zhu Nie;Xiao-Long Chen;Department of Ophthalmology, Shengjing Hospital of China Medical University;',
            'abstract': 'Inhibiting retinal neovascularization is the optimal strategy for the treatment of retina-related diseases, but there is currently no effective treatment for retinal neovascularization. P-element-induced wimpy testis（PIWI）-interacting RNA（piRNA） is a type of small non-coding RNA implicated in a variety of diseases. In this study, we found that the expression of piR-1245 and the interacting protein PIWIL2 were remarkably increased in human retinal endothelial cells cultured in a hypoxic environment, and cell apoptosis, migration, tube formation and proliferation were remarkably enhanced in these cells. Knocking down piR-1245 inhibited the above phenomena. After intervention by a p-JAK2 activator, piR-1245 decreased the expression of hypoxia inducible factor-1α and vascular endothelial growth factor through the JAK2/STAT3 pathway. For in vivo analysis, 7-day-old newborn mice were raised in 75 ± 2% hyperoxia for 5 days and then piR-1245 in the retina was knocked down. In these mice, the number of newly formed vessels in the retina was decreased, the expressions of inflammationrelated proteins were reduced, the number of apoptotic cells in the retina was decreased, the JAK2/STAT3 pathway was inhibited, and the expressions of hypoxia inducible factor-1α and vascular endothelial growth factor were decreased. Injection of the JAK2 inhibitor JAK2/TYK2-IN-1 into the vitreous cavity inhibited retinal neovascularization in mice and reduced expression of hypoxia inducible factor-1α and vascular endothelial growth factor. These findings suggest that piR-1245 activates the JAK2/STAT3 pathway, regulates the expression of hypoxia inducible factor-1α and vascular endothelial growth factor, and promotes retinal neovascularization. Therefore, piR-1245 may be a new therapeutic target for retinal neovascularization.',
            'keywords': 'angiogenesis;\rhumanretinalendothelialcells;\rhypoxiainduciblefactor-1α;\rhypoxia;\rinterleukin-1β;\rmigration;\rnon-codingRNA;\roxygen-inducedinjury;\rPIWI-interactingRNA;\rretinopathy;\r',
            'fund': 'supportedbytheNationalNaturalScienceFoundationofChina,No.81570866（toXLC）；\r', 'doi': '',
            'series': '(E) Medicine ＆ Public Health', 'subject': 'Ophthalmology and Otolaryngology', 'clc': 'R774.1',
            'journal_name': '中国神经再生研究(英文版).\r;2023(05)\r;\rPage:1132-1138'}
        data_list = item.CsvItem(data_storage='./', filename='test')
        data_list.append(aaa)
        yield data_list


if __name__ == "__main__":
    RetryDemo.start(middleware=middleware)
