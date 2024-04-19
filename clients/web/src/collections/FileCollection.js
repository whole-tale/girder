import { SORT_DESC } from 'girder/constants';
import Collection from 'girder/collections/Collection';
import FileModel from 'girder/models/FileModel';

var FileCollection = Collection.extend({
    resourceName: 'file',
    model: FileModel,

    sortField: 'created',
    sortDir: SORT_DESC,
    pageLimit: 100
});

export default FileCollection;
